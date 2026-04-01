Fetches weather info using an API
"""
Advanced Weather API Client with Caching, Rate Limiting, and Analytics
Fetches weather data from multiple sources with intelligent retry logic
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib
import time


@dataclass
class WeatherData:
    """Weather data structure"""
    location: str
    temperature: float
    humidity: int
    pressure: float
    wind_speed: float
    description: str
    timestamp: datetime
    source: str
    
    def to_json(self) -> str:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return json.dumps(data, indent=2)


class RateLimiter:
    """Token bucket rate limiter"""
    def __init__(self, requests_per_minute: int = 60):
        self.capacity = requests_per_minute
        self.tokens = requests_per_minute
        self.last_update = time.time()
        self.rate = requests_per_minute / 60.0
    
    async def acquire(self):
        while True:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return
            
            await asyncio.sleep(0.1)


class CacheManager:
    """LRU cache with TTL"""
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.cache: Dict[str, Tuple[any, datetime]] = {}
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self.access_order: List[str] = []
    
    def _generate_key(self, *args) -> str:
        key_string = ''.join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, *args) -> Optional[any]:
        key = self._generate_key(*args)
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                # Move to end (most recently used)
                self.access_order.remove(key)
                self.access_order.append(key)
                return value
            else:
                del self.cache[key]
                self.access_order.remove(key)
        return None
    
    def set(self, value: any, *args):
        key = self._generate_key(*args)
        
        # Evict LRU if cache is full
        if len(self.cache) >= self.max_size and key not in self.cache:
            lru_key = self.access_order.pop(0)
            del self.cache[lru_key]
        
        self.cache[key] = (value, datetime.now())
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)


class WeatherAnalytics:
    """Analytics for weather data"""
    def __init__(self):
        self.history: List[WeatherData] = []
        self.source_stats = defaultdict(int)
    
    def add_data(self, data: WeatherData):
        self.history.append(data)
        self.source_stats[data.source] += 1
    
    def get_average_temperature(self, hours: int = 24) -> Optional[float]:
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [d.temperature for d in self.history if d.timestamp > cutoff]
        return sum(recent) / len(recent) if recent else None
    
    def get_temperature_trend(self) -> str:
        """Analyze temperature trend over last measurements"""
        if len(self.history) < 2:
            return "insufficient_data"
        
        recent = self.history[-5:]  # Last 5 measurements
        temps = [d.temperature for d in recent]
        
        if all(temps[i] < temps[i+1] for i in range(len(temps)-1)):
            return "rising"
        elif all(temps[i] > temps[i+1] for i in range(len(temps)-1)):
            return "falling"
        else:
            return "stable"
    
    def generate_report(self) -> Dict:
        return {
            "total_requests": len(self.history),
            "sources": dict(self.source_stats),
            "avg_temp_24h": self.get_average_temperature(),
            "temperature_trend": self.get_temperature_trend(),
            "latest_reading": self.history[-1].to_json() if self.history else None
        }


class WeatherAPIClient:
    """Advanced weather API client with multiple features"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.rate_limiter = RateLimiter(requests_per_minute=60)
        self.cache = CacheManager(max_size=100, ttl_seconds=600)
        self.analytics = WeatherAnalytics()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _fetch_with_retry(self, url: str, max_retries: int = 3) -> Dict:
        """Fetch data with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                await self.rate_limiter.acquire()
                
                async with self.session.get(url, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limited
                        wait_time = 2 ** attempt
                        await asyncio.sleep(wait_time)
                    else:
                        response.raise_for_status()
            
            except asyncio.TimeoutError:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
            
            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
    
    async def get_weather(self, city: str, use_cache: bool = True) -> WeatherData:
        """Fetch current weather for a city"""
        
        # Check cache first
        if use_cache:
            cached = self.cache.get(city)
            if cached:
                print(f"📦 Cache hit for {city}")
                return cached
        
        # Build URL
        url = f"{self.base_url}/weather?q={city}&appid={self.api_key}&units=metric"
        
        # Fetch data
        data = await self._fetch_with_retry(url)
        
        # Parse response
        weather = WeatherData(
            location=data['name'],
            temperature=data['main']['temp'],
            humidity=data['main']['humidity'],
            pressure=data['main']['pressure'],
            wind_speed=data['wind']['speed'],
            description=data['weather'][0]['description'],
            timestamp=datetime.now(),
            source='openweathermap'
        )
        
        # Update cache and analytics
        self.cache.set(weather, city)
        self.analytics.add_data(weather)
        
        return weather
    
    async def get_bulk_weather(self, cities: List[str]) -> List[WeatherData]:
        """Fetch weather for multiple cities concurrently"""
        tasks = [self.get_weather(city) for city in cities]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_analytics_report(self) -> Dict:
        """Get analytics report"""
        return self.analytics.generate_report()


# Example usage
async def main():
    API_KEY = "your_api_key_here"  # Replace with actual API key
    
    async with WeatherAPIClient(API_KEY) as client:
        # Single city
        print("🌍 Fetching weather for Kyiv...")
        weather = await client.get_weather("Kyiv")
        print(weather.to_json())
        
        # Multiple cities concurrently
        print("\n🌍 Fetching weather for multiple cities...")
        cities = ["London", "Paris", "Tokyo", "New York", "Sydney"]
        results = await client.get_bulk_weather(cities)
        
        for result in results:
            if isinstance(result, WeatherData):
                print(f"\n{result.location}: {result.temperature}°C - {result.description}")
        
        # Analytics
        print("\n📊 Analytics Report:")
        report = client.get_analytics_report()
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

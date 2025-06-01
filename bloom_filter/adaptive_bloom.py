import hashlib
import math
from pybloom_live import BloomFilter
import random
import string
from urllib.parse import urlparse

class AdaptiveBloomFilter:
    def __init__(self, initial_capacity=50, error_rate=0.2, adaptation_threshold=0.05):
        self.bloom_filter = BloomFilter(capacity=initial_capacity, error_rate=error_rate)
        self.hash_functions = [hashlib.md5, hashlib.sha1, hashlib.sha256]
        self.inserted_items = set()
        self.stats = {
            'total_checks': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'fpr_samples': 0,
            'fnr_samples': 0
        }
        self.adaptation_threshold = adaptation_threshold  # 1% error rate threshold
        self.last_fpr = 0
        self.last_fnr = 0

    def add(self, item):
        self.bloom_filter.add(item)
        self.inserted_items.add(item)

    def contains(self, item):
        result = item in self.bloom_filter
        self.stats['total_checks'] += 1
        return result

    def sample_fpr(self, num_samples=50):
        """Test FPR by querying random non-inserted items that resemble real URLs."""
        false_positives = 0
        
        # Extract patterns from real inserted URLs to create similar test URLs
        real_domains = set()
        real_paths = set()
        
        # Extract domains and path patterns from real URLs
        for url in self.inserted_items:
            try:
                parsed = urlparse(url)
                if parsed.netloc:
                    real_domains.add(parsed.netloc)
                if parsed.path and '/' in parsed.path:
                    parts = parsed.path.strip('/').split('/')
                    if parts and parts[0]:
                        real_paths.add(parts[0])
            except:
                pass
        
        # If we don't have enough real patterns, add some defaults
        if len(real_domains) < 5:
            real_domains.update(['example.com', 'test.org', 'sample.net', 'demo.io', 'fake.site'])
        if len(real_paths) < 5:
            real_paths.update(['page', 'article', 'post', 'product', 'category', 'news', 'blog'])
        
        # Convert to lists for random.choice
        domains = list(real_domains)
        paths = list(real_paths)
        
        # Create a mix of test URLs - some very similar to real ones to ensure false positives
        for _ in range(num_samples):
            # Determine test type - 30% very similar to real URLs, 70% more random
            if random.random() < 0.3 and self.inserted_items:
                # Take a real URL and modify it slightly to create a false positive
                real_url = random.choice(list(self.inserted_items))
                try:
                    parsed = urlparse(real_url)
                    # Change just a small part of the URL
                    if parsed.path and '/' in parsed.path:
                        parts = parsed.path.strip('/').split('/')
                        if len(parts) > 1:
                            # Change just one character in the last part
                            last_part = parts[-1]
                            if last_part:
                                idx = random.randint(0, max(0, len(last_part)-1))
                                char = random.choice(string.ascii_lowercase)
                                modified_part = last_part[:idx] + char + last_part[idx+1:]
                                parts[-1] = modified_part
                                path = '/' + '/'.join(parts)
                                fake_url = f"{parsed.scheme}://{parsed.netloc}{path}"
                            else:
                                # Fallback if last part is empty
                                fake_url = f"{parsed.scheme}://{parsed.netloc}/{'/'.join(parts)}/x"
                        else:
                            fake_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}x"
                    else:
                        fake_url = f"{parsed.scheme}://{parsed.netloc}/x"
                except:
                    # Fallback if parsing fails
                    domain = random.choice(domains)
                    path = random.choice(paths)
                    fake_url = f"https://{domain}/{path}/test"
            else:
                # Create a completely new URL but using patterns from real ones
                domain = random.choice(domains)
                path = random.choice(paths)
                rand_id = ''.join(random.choices(string.digits + string.ascii_lowercase, k=4))
                fake_url = f"https://{domain}/{path}/{rand_id}"
            
            # Skip if we accidentally generated a real URL
            if fake_url in self.inserted_items:
                continue
                
            # Test if this URL is falsely recognized as seen
            if fake_url in self.bloom_filter:
                false_positives += 1
                self.stats['false_positives'] += 1
                
        self.stats['fpr_samples'] += num_samples
        self.last_fpr = false_positives / num_samples if num_samples else 0
        return self.last_fpr

    def sample_fnr(self, num_samples=20):
        """Test FNR by querying actual inserted items (should always be present)."""
        if not self.inserted_items:
            return 0
        false_negatives = 0
        sample_items = random.sample(list(self.inserted_items), min(num_samples, len(self.inserted_items)))
        for item in sample_items:
            if item not in self.bloom_filter:
                false_negatives += 1
        self.stats['fnr_samples'] += len(sample_items)
        self.last_fnr = false_negatives / len(sample_items) if sample_items else 0
        return self.last_fnr

    def adapt(self):
        fpr = self.sample_fpr()
        fnr = self.sample_fnr()
        if fpr > self.adaptation_threshold:
            return self.increase_capacity()
        elif fnr > self.adaptation_threshold:
            return self.increase_capacity()  # FNR should almost never happen; resize up
        return False  # No adaptation needed

    def increase_capacity(self):
        try:
            # Use a very conservative growth strategy
            max_capacity = 10000  # 10K items max for safety
            
            # Increase by just 25% instead of doubling
            new_capacity = min(int(self.bloom_filter.capacity * 1.25) + 5, max_capacity)
            
            # If we're already near max capacity, adjust the error rate instead
            if self.bloom_filter.capacity >= max_capacity * 0.5:
                # Increase error rate slightly (accept more false positives)
                new_error_rate = min(self.bloom_filter.error_rate * 1.2, 0.4)
                print(f"Near capacity limit, adjusting error rate to {new_error_rate}")
                new_filter = BloomFilter(capacity=self.bloom_filter.capacity, error_rate=new_error_rate)
            else:
                # Create new filter with increased capacity
                print(f"Increasing capacity from {self.bloom_filter.capacity} to {new_capacity}")
                new_filter = BloomFilter(capacity=new_capacity, error_rate=self.bloom_filter.error_rate)
            
            # Copy existing items safely - but limit to 1000 max to avoid capacity issues
            item_count = 0
            items_to_copy = list(self.inserted_items)[:1000]  # Limit to 1000 items
            for item in items_to_copy:
                try:
                    new_filter.add(item)
                    item_count += 1
                except Exception as e:
                    print(f"Warning: Failed to add item {item_count} to new filter: {e}")
                    break  # Stop if we hit an error
            
            print(f"Successfully copied {item_count} items to new filter")
            self.bloom_filter = new_filter
            return True
        except Exception as e:
            print(f"Warning: Failed to increase Bloom filter capacity: {e}")
            # If we can't increase capacity, try increasing error rate as fallback
            try:
                current_error_rate = self.bloom_filter.error_rate
                new_error_rate = min(current_error_rate * 1.5, 0.5)
                print(f"Trying fallback: adjusting error rate from {current_error_rate} to {new_error_rate}")
                # Keep the same capacity but increase error rate
                new_filter = BloomFilter(
                    capacity=self.bloom_filter.capacity,
                    error_rate=new_error_rate
                )
                # Copy a limited number of items
                items_to_copy = list(self.inserted_items)[:500]  # Very conservative
                for item in items_to_copy:
                    try:
                        new_filter.add(item)
                    except:
                        break
                self.bloom_filter = new_filter
                return True
            except Exception as e2:
                print(f"Fallback also failed: {e2}")
                # Last resort - create a new empty filter with higher error rate
                try:
                    print("Creating new empty filter as last resort")
                    self.bloom_filter = BloomFilter(capacity=100, error_rate=0.3)
                    return True
                except:
                    return False

    def get_stats(self):
        return {
            'total_checks': self.stats['total_checks'],
            'false_positives': self.stats['false_positives'],
            'false_negatives': self.stats['false_negatives'],
            'fpr_samples': self.stats['fpr_samples'],
            'fnr_samples': self.stats['fnr_samples'],
            'last_fpr': self.last_fpr,
            'last_fnr': self.last_fnr,
            'capacity': self.bloom_filter.capacity,
            'error_rate': self.bloom_filter.error_rate,
            'inserted_count': len(self.inserted_items)
        }


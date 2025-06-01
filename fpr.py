import matplotlib.pyplot as plt

# Example data
url_counts = [10000, 20000, 40000, 60000, 80000, 100000]
fixed_fpr = [0.01, 0.025, 0.045, 0.07, 0.11, 0.16]     # Example: FPR rises with more URLs
adaptive_fpr = [0.01, 0.012, 0.015, 0.017, 0.019, 0.021] # Example: Adaptive stays low

plt.figure(figsize=(6,4))
plt.plot(url_counts, fixed_fpr, marker='o', label='Fixed Bloom Filter')
plt.plot(url_counts, adaptive_fpr, marker='s', label='Adaptive Bloom Filter')
plt.xlabel('Number of Unique URLs')
plt.ylabel('False Positive Rate')
plt.title('False Positive Rate Comparison')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('fpr_comparison.png', dpi=300)
plt.show()
"""
Download datasets for NeuroChain Demo.
Run this script once before launching the demo.
"""
import os

def download_datasets():
    os.makedirs("datasets", exist_ok=True)
    
    print("Downloading datasets using scikit-learn...")
    
    # 1. Cancer Dataset
    from sklearn.datasets import load_breast_cancer
    import pandas as pd
    
    cancer = load_breast_cancer()
    df_cancer = pd.DataFrame(cancer.data, columns=cancer.feature_names)
    df_cancer['diagnosis'] = ['M' if t == 0 else 'B' for t in cancer.target]
    df_cancer.insert(0, 'id', range(1, len(df_cancer) + 1))
    df_cancer.to_csv("datasets/cancer.csv", index=False)
    print(f"  [OK] datasets/cancer.csv ({len(df_cancer)} rows)")
    
    # 2. Wine Dataset
    from sklearn.datasets import load_wine
    wine = load_wine()
    df_wine = pd.DataFrame(wine.data, columns=wine.feature_names)
    # Create a 'quality' column (scale 1-10) from the target classes
    import numpy as np
    df_wine['quality'] = np.where(wine.target == 0, 4, np.where(wine.target == 1, 6, 8))
    df_wine.to_csv("datasets/wine.csv", sep=";", index=False)
    print(f"  [OK] datasets/wine.csv ({len(df_wine)} rows)")
    
    # 3. Digits Dataset
    from sklearn.datasets import load_digits
    digits = load_digits()
    df_digits = pd.DataFrame(digits.data)
    df_digits[len(digits.data[0])] = digits.target  # Last column is label
    df_digits.to_csv("datasets/digits.csv", index=False, header=False)
    print(f"  [OK] datasets/digits.csv ({len(df_digits)} rows)")
    
    print("\nAll datasets downloaded successfully!")
    print("You can now run: python neurochain_demo.py")

if __name__ == "__main__":
    download_datasets()

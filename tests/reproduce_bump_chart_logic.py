
import pandas as pd
import numpy as np

def reproduce_logic():
    # Mock data:
    # Year 2024: Author A is #1 (100 counts), Author B is #2 (90), ..., Author F is #6 (10)
    # Year 2025: Author A is #6 (20 counts), Others are higher.
    
    data = []
    
    # 2024
    for _ in range(100): data.append({'analysis_date': '2024-01-01', 'author': 'Author A', 'category': 'Post'})
    for _ in range(90): data.append({'analysis_date': '2024-01-01', 'author': 'Author B', 'category': 'Post'})
    for _ in range(80): data.append({'analysis_date': '2024-01-01', 'author': 'Author C', 'category': 'Post'})
    for _ in range(70): data.append({'analysis_date': '2024-01-01', 'author': 'Author D', 'category': 'Post'})
    for _ in range(60): data.append({'analysis_date': '2024-01-01', 'author': 'Author E', 'category': 'Post'})
    for _ in range(50): data.append({'analysis_date': '2024-01-01', 'author': 'Author F', 'category': 'Post'}) # Rank 6
    
    # 2025
    # Author A drops to 20 counts.
    # We need 5 authors with > 20 counts to push Author A out of Top 5.
    for _ in range(100): data.append({'analysis_date': '2025-01-01', 'author': 'Author B', 'category': 'Post'})
    for _ in range(90): data.append({'analysis_date': '2025-01-01', 'author': 'Author C', 'category': 'Post'})
    for _ in range(80): data.append({'analysis_date': '2025-01-01', 'author': 'Author D', 'category': 'Post'})
    for _ in range(70): data.append({'analysis_date': '2025-01-01', 'author': 'Author E', 'category': 'Post'})
    for _ in range(60): data.append({'analysis_date': '2025-01-01', 'author': 'Author F', 'category': 'Post'})
    for _ in range(20): data.append({'analysis_date': '2025-01-01', 'author': 'Author A', 'category': 'Post'}) # 20 counts
    
    df = pd.DataFrame(data)
    
    # Logic from instagram.py
    df['year'] = pd.to_datetime(df['analysis_date']).dt.year
    authors_df = df[df['author'] != 'Unknown']
    
    author_data = authors_df.groupby(['year', 'author']).size().reset_index(name='engagement_count')
    
    print("\n--- Raw Counts ---")
    print(author_data[author_data['author'] == 'Author A'])
    
    bump_data = author_data.groupby('year').apply(lambda x: x.nlargest(5, 'engagement_count')).reset_index(drop=True)
    bump_data['rank'] = bump_data.groupby('year')['engagement_count'].rank(ascending=False, method='first')
    
    print("\n--- Bump Chart Data (Top 5 per year) ---")
    print(bump_data)
    
    # Check if Author A is in 2025 bump data
    author_a_2025 = bump_data[(bump_data['year'] == 2025) & (bump_data['author'] == 'Author A')]
    if author_a_2025.empty:
        print("\n[RESULT] Author A is NOT in the 2025 visualization (Ranked > 5).")
    else:
        print("\n[RESULT] Author A IS in the 2025 visualization.")
        print(author_a_2025)

if __name__ == "__main__":
    reproduce_logic()

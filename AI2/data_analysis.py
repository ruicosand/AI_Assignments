import pandas as pd
import os

def load_and_view_data():
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, 'data')
    output_file = os.path.join(base_dir, 'data_summary.txt')
    
    if not os.path.exists(data_dir):
        print(f"Data directory not found at: {data_dir}")
        return
        
    files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]
    
    if not files:
        print("No Excel files found in the data directory.")
        return
        
    # Set pandas options for better readability in text format
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_colwidth', 50)
        
    with open(output_file, 'w') as f_out:
        for file in files:
            file_path = os.path.join(data_dir, file)
            f_out.write(f"--- Viewing data from: {file} ---\n")
            try:
                df = pd.read_excel(file_path)
                f_out.write(f"Shape: {df.shape}\n")
                f_out.write(f"Columns: {df.columns.tolist()}\n")
                f_out.write("\nFirst 5 rows:\n")
                # Exclude MeterValues fully if it exists or truncate it since colwidth limits it
                f_out.write(df.head().to_string())
                f_out.write("\n\n" + "="*80 + "\n\n")
            except Exception as e:
                f_out.write(f"Error reading {file}: {e}\n\n")
                
    print(f"Data analysis successfully saved to {output_file} in a readable format")

if __name__ == "__main__":
    load_and_view_data()

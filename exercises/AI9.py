import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# Load the dataset
data = pd.read_excel('IART_9_clustering.xlsx', sheet_name='catalog')


#desired = data
#desired = data[['Total LTD Orders', 'Total 24 Month Orders', 'Number of Divisns w/ Purchase', 'Number of Credit Cards Used', 'Customer Gender', 'Different Day/Night Phone (yes=1)', 'Dwelling Type Indicator', 'Overall RFM Points', 'First Purch Mail Order (yes=1)']]
desired = data[['Total LTD Orders', 'Overall RFM Points']]


scaler = StandardScaler()
scaled_features = scaler.fit_transform(desired)
#scaled_features = desired


model = KMeans(n_clusters=2, random_state=42)
data['cluster'] = model.fit_predict(scaled_features)


# VISUALIZATION: Plotting original columns directly
plt.figure(figsize=(10, 6)) 

# Use the original columns from 'data' for the axes to avoid negative/scaled values
plt.scatter(data['Total LTD Orders'], data['Overall RFM Points'], 
            c=data['cluster'], cmap='viridis', alpha=0.6)

plt.title('Catalog Customer Segments')
plt.xlabel('Total LTD Orders')
plt.ylabel('Overall RFM Points')
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()


# 1. create pca projection for visualization
pca = PCA(n_components=2)
pca_data = pca.fit_transform(scaled_features)

# 2. plot the pca clusters
plt.figure(figsize=(10, 6))
plt.scatter(pca_data[:, 0], pca_data[:, 1], c=data['cluster'], cmap='viridis', alpha=0.5)
plt.title('cluster visualization using pca (2d projection)')
plt.xlabel('Total Lifetime-to-Date (LTD) Orders')
plt.ylabel('Overall RFM Score (Recency, Frequency, Monetary)')
plt.colorbar(label='cluster')
plt.show()

# 3. plot the average values for each cluster to see their differences
features_list = ['Total LTD Orders', 'Overall RFM Points']
cluster_means = data.groupby('cluster')[features_list].mean().T

cluster_means.plot(kind='bar', figsize=(12, 6))
plt.title('average feature values per cluster')
plt.ylabel('average value')
plt.xticks(rotation=45)
plt.show()


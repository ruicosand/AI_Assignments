import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import silhouette_score, mean_absolute_error, r2_score
import matplotlib.pyplot as plt 
import numpy as np


dataset = pd.read_excel("data/all_chargers_pivoted.xlsx")

dataset = dataset.sort_values('Timestamp')

power = 7.5       # kW — potência média medida nos primeiros minutos
consumption = 15

# forecasting
sessions_ids = dataset.groupby('Id').agg({
    "DurationInMinutes": "first",
    "ChargePointId": "first",
    "Power.Active.Import": "mean",
    "Consumption": "first"
})

sessions_ids = sessions_ids.dropna()

n = sessions_ids.shape[0]

train_data = sessions_ids.head(int(n * 0.70)).copy()

test_data = sessions_ids.tail(int(n * 0.30)).copy()

modelForecast = DecisionTreeRegressor(max_depth=5, random_state=42)


modelForecast.fit(train_data[['Consumption','Power.Active.Import']], train_data['DurationInMinutes'])


previsions = modelForecast.predict(test_data[['Consumption','Power.Active.Import']])


r2Score = r2_score(test_data['DurationInMinutes'], previsions)


meanErrorScore = mean_absolute_error(test_data['DurationInMinutes'], previsions)


print("-------- Forecasting --------\n")
print("Importance of the features in the decision tree:")
print("\n")
print(modelForecast.feature_importances_)
print("R²: ", r2Score)
print("\n")
print("MAE: ", meanErrorScore)

# Sessão quase no início
inicio = pd.DataFrame([[2, 7.5]], columns=['Consumption', 'Power.Active.Import'])
print(f"Início da sessão: {modelForecast.predict(inicio)[0]:.1f} minutos")

# Sessão a meio
meio = pd.DataFrame([[10, 7.5]], columns=['Consumption', 'Power.Active.Import'])
print(f"A meio da sessão: {modelForecast.predict(meio)[0]:.1f} minutos")

# Sessão quase no fim
fim = pd.DataFrame([[22, 7.5]], columns=['Consumption', 'Power.Active.Import'])
print(f"Quase no fim: {modelForecast.predict(fim)[0]:.1f} minutos")

'''
# anomaly detection

eletric_values = ['Current.Import_L1','Current.Import_L2',"Current.Import_L3","Power.Active.Import","Power.Offered" ,"Voltage_L1", "Voltage_L2", "Voltage_L3"]

information_values = ['ChargePointId', 'ConnectorId', 'Timestamp']

anomaly_features = dataset[ information_values + eletric_values]

anomaly_features = anomaly_features.dropna()

n = anomaly_features.shape[0]

train_data = anomaly_features.head(int(n * 0.70)).copy()

test_data = anomaly_features.tail(int(n * 0.30)).copy()


model = IsolationForest(contamination=0.05)

model.fit(train_data[eletric_values])

isAnomaly = model.predict(test_data[eletric_values])

anomaly_score = model.score_samples(test_data[eletric_values])


test_data['isAnomaly'] = isAnomaly
test_data['AnomScore'] = anomaly_score

test_data = test_data.sort_values('AnomScore')


test_data_anomalies = test_data[test_data['isAnomaly'] == -1]

chargers = test_data_anomalies.groupby('ChargePointId').count().sort_values('isAnomaly', ascending=False)
anomaly_descript = []

for charger_id in chargers.index:

    charger_anomaly = test_data_anomalies[test_data_anomalies['ChargePointId'] == charger_id].sort_values('AnomScore')

    # tensão

    tension_information = charger_anomaly.head(20)[['Voltage_L1', 'Voltage_L2', 'Voltage_L3']].describe()


    mean_value = tension_information.loc['mean']
    

    if not (220 < mean_value['Voltage_L1'] < 240):
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Voltage_L1 out of standards',
            'Voltage_L1': mean_value['Voltage_L1'],
            'Voltage_L2': mean_value['Voltage_L2'],
            'Voltage_L3': mean_value['Voltage_L3'],
        })


    if not (220 < mean_value['Voltage_L2'] < 240):
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Voltage_L2 out of standards',
            'Voltage_L1': mean_value['Voltage_L1'],
            'Voltage_L2': mean_value['Voltage_L2'],
            'Voltage_L3': mean_value['Voltage_L3'],
        })

    if not (220 < mean_value['Voltage_L3'] < 240):
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Voltage_L3 out of standards',
            'Voltage_L1': mean_value['Voltage_L1'],
            'Voltage_L2': mean_value['Voltage_L2'],
            'Voltage_L3': mean_value['Voltage_L3'],
        })


    if abs(mean_value['Voltage_L1'] - mean_value['Voltage_L2']) > 10:
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Difference between Phases 1 and 2 out of standards',
            'Voltage_L1': mean_value['Voltage_L1'],
            'Voltage_L2': mean_value['Voltage_L2'],
            'Voltage_L3': mean_value['Voltage_L3'],
        })

    if abs(mean_value['Voltage_L1'] - mean_value['Voltage_L3']) > 10:
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Difference between Phases 1 and 2 out of standards',
            'Voltage_L1': mean_value['Voltage_L1'],
            'Voltage_L2': mean_value['Voltage_L2'],
            'Voltage_L3': mean_value['Voltage_L3'],
        })

    if abs(mean_value['Voltage_L2'] - mean_value['Voltage_L3']) > 10:
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Difference between Phases 1 and 2 out of standards',
            'Voltage_L1': mean_value['Voltage_L1'],
            'Voltage_L2': mean_value['Voltage_L2'],
            'Voltage_L3': mean_value['Voltage_L3'],
        })



    # corrente 

    corrent_information = charger_anomaly.head(20).copy()

    corrent_information['equilibrio_L1_L2'] = (corrent_information['Current.Import_L1'] == 0)  & (corrent_information['Current.Import_L2'] > 0) & (corrent_information['Current.Import_L3'] > 0)

    corrent_information['equilibrio_L2_L1'] = (corrent_information['Current.Import_L2'] == 0)  & (corrent_information['Current.Import_L1'] > 0) & (corrent_information['Current.Import_L3'] > 0)

    corrent_information['equilibrio_L3_L1'] = (corrent_information['Current.Import_L3'] == 0)  & (corrent_information['Current.Import_L1'] > 0) & (corrent_information['Current.Import_L2'] > 0)


    corrent_information['desequilibrio_L1_L2'] = abs(corrent_information['Current.Import_L1'] - corrent_information['Current.Import_L2']) > 2

    corrent_information['desequilibrio_L1_L3'] = abs(corrent_information['Current.Import_L1'] - corrent_information['Current.Import_L3']) > 2

    corrent_information['desequilibrio_L2_L3'] = abs(corrent_information['Current.Import_L2'] - corrent_information['Current.Import_L3']) > 2

    if corrent_information['equilibrio_L1_L2'].any():
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Corrent with different values',
            'Current.Import_L1': corrent_information['Current.Import_L1'].mean(),
            'Current.Import_L2': corrent_information['Current.Import_L2'].mean(),
            'Current.Import_L3': corrent_information['Current.Import_L3'].mean(),
        })

    if corrent_information['equilibrio_L2_L1'].any():
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Corrent with different values',
            'Current.Import_L1': corrent_information['Current.Import_L1'].mean(),
            'Current.Import_L2': corrent_information['Current.Import_L2'].mean(),
            'Current.Import_L3': corrent_information['Current.Import_L3'].mean(),
        })

    if corrent_information['equilibrio_L3_L1'].any():
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Corrent with different values',
            'Current.Import_L1': corrent_information['Current.Import_L1'].mean(),
            'Current.Import_L2': corrent_information['Current.Import_L2'].mean(),
            'Current.Import_L3': corrent_information['Current.Import_L3'].mean(),
        })

    if corrent_information['desequilibrio_L1_L2'].any():
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Corrent with different values',
            'Current.Import_L1': corrent_information['Current.Import_L1'].mean(),
            'Current.Import_L2': corrent_information['Current.Import_L2'].mean(),
            'Current.Import_L3': corrent_information['Current.Import_L3'].mean(),
        })

    if corrent_information['desequilibrio_L1_L3'].any():
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Corrent with different values',
            'Current.Import_L1': corrent_information['Current.Import_L1'].mean(),
            'Current.Import_L2': corrent_information['Current.Import_L2'].mean(),
            'Current.Import_L3': corrent_information['Current.Import_L3'].mean(),
        })

    if corrent_information['desequilibrio_L2_L3'].any():
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Corrent with different values',
            'Current.Import_L1': corrent_information['Current.Import_L1'].mean(),
            'Current.Import_L2': corrent_information['Current.Import_L2'].mean(),
            'Current.Import_L3': corrent_information['Current.Import_L3'].mean(),
        })



    # potência

    potency_information = charger_anomaly.head(50).copy()

    potency_information['powerDifference'] = abs(potency_information['Power.Offered'] - potency_information['Power.Active.Import']) > 2


    if potency_information['powerDifference'].any():
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Potency with a difference above 2 kW',
            'Power_Offered': potency_information['Power.Offered'].mean(),
            'Power.Active.Import': potency_information['Power.Active.Import'].mean()
        })

    potency_information["Power"] = (potency_information['Voltage_L1'] * potency_information['Current.Import_L1'] + potency_information['Voltage_L2'] * potency_information['Current.Import_L2']
                                    + potency_information['Voltage_L3'] * potency_information['Current.Import_L3']) / 1000

    potency_information['Power_Diff'] = abs(potency_information["Power"] - potency_information["Power.Active.Import"]) > 1

    if potency_information['Power_Diff'].any():
        anomaly_descript.append({
            'ChargePointId': charger_id,
            'AnomalyType': 'Power superior a 1',
            'Power': potency_information['Power'].mean(),
            'Power.Active.Import': potency_information['Power.Active.Import'].mean()
        })

    else:
        print("Nothing to report")


inertias = []
silhouette_scores = []
anomaly_df = pd.DataFrame(anomaly_descript)
anomaly_df = anomaly_df.fillna(0)

numeric_cols = anomaly_df.select_dtypes(include='number').columns.tolist()

for k in range(2, 7):      
    model = KMeans(n_clusters=k)
    model.fit(anomaly_df[numeric_cols])    
    inertias.append(model.inertia_)
    score = silhouette_score(anomaly_df[numeric_cols], model.labels_)
    silhouette_scores.append(score)


x = [i for i in range(2, 7)]
y = silhouette_scores


final_model = KMeans(n_clusters=3)
final_model.fit(anomaly_df[numeric_cols])
anomaly_df['Cluster'] = final_model.labels_

print(anomaly_df.groupby('Cluster')['AnomalyType'].value_counts())
print(anomaly_df.groupby('Cluster')['ChargePointId'].value_counts())

'''
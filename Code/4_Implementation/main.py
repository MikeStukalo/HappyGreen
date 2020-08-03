'''
Putt prediction app
'''

import pandas as pd
import numpy as np
from catboost import CatBoostClassifier
import DetectPutt as DP
import CollectData as CD
import os


def MakePrediction(distance, df, lower_bound_AZ, window, margin, model):
    '''
    Uses raw observation data to make a prediction
    '''
    # Extract features
    putt = DP.Putt(df, lower_bound_AZ, window, margin)

    feats = putt.features()

    # Check that features were extracted
    if feats.shape[0] != 1:
        return([np.nan])

    else:
        # Create dataset for the  model
        feats['Distance'] = distance
        #feats.drop('Id', axis=1, inplace=True)
        feats = feats[model.feature_names_]
        print(feats)
        pred = model.predict(feats)

        return(pred)


if __name__ == "__main__":

    # Set MacAddress
    mac = "C0:83:3A:30:5D:47"

    # Load the model
    model = CatBoostClassifier()
    model.load_model("./data/catboost_model.cb")

    # Set input arguments
    lower_bound_AZ = -300  # For AZ
    window = 50
    margin = 25  # Left margin if we detected a first break through

    # Distance
    distance = input("Enter approximate distance in feet: ")

    try:
        float(distance)

    except ValueError:
        print('Enter numeric only')

    df = CD.CollectData(mac)

    # Pad df to have enough observations
    pad = df.replace(df, 0)
    df = pad.append(df, ignore_index=True).append(pad, ignore_index=True)

    pr = MakePrediction(distance, df, lower_bound_AZ, window, margin, model)

    if pr[0] == 0:
        print('Miss')
        os.system('spd-say "You Miss"')

    elif pr[0] == 0:
        print('Scored')
        os.system('spd-say "You Scored"')

    else:
        print('No putt detected')
        os.system('spd-say "No putt detected"')

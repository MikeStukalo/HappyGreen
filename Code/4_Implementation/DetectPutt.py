'''
Set of functions to detect a putt and label putt stages
'''

import pandas as pd
import numpy as np


# Helper functions

# Function to detect putt points
def DetectPuttPoints(df, lower_bound_AZ, window=100, margin=25):
    '''
    Function to detect several parts of a putt - swing back, swing forward

    Returns a dataframe with orgignal data and marks: 1 - beginning of a swing back ,
    2 - beginnig of swing forward, 3 - end of swing forward

    '''

    df = df.set_index('Time')
    df['Mark'] = np.nan

    # Scan through the dataframe
    i = 0
    while i < (df.shape[0] - window):
        tmp = df.iloc[i:(i + window), :]

        # Found break through
        if tmp.AZ.min() < lower_bound_AZ:

            # Step left by margin and find beginning of the swing
            # Find index of the min
            mark_ind = tmp.loc[tmp.AZ == tmp.AZ.min(), :].index.values[0]
            ind_num = df.index.get_loc(mark_ind)

            # Left part of the window
            tmp1 = df.iloc[(ind_num - margin):ind_num, :]
            mark_1_ind = tmp1.loc[tmp1.AZ == tmp1.AZ.max(), :].index.values[0]

            #  All window
            tmp2 = df.iloc[(ind_num - margin):(ind_num - margin + window), :]
            # End of the swing forward
            mark_3_ind = tmp2.loc[tmp2.AZ == tmp2.AZ.max(), :].index.values[0]

            mark_2_ind = tmp2.loc[tmp2.AZ == tmp2.loc[mark_1_ind:mark_3_ind, 'AZ'].min(
            ), :].index.values[0]  # Beginning of the swing forward

            df.at[mark_1_ind, 'Mark'] = 1  # Mark beginning of swing backward
            df.at[mark_2_ind, 'Mark'] = 2  # Mark beginning of swing forward
            df.at[mark_3_ind, 'Mark'] = 3  # Mark end of swing forward

            # Reset i
            i = ind_num - margin + window

        else:
            i += 1
            continue  # Continue scan

    return df


# Function to mark correct puts
def MarkPutts(df, lower_bound_AZ, window, margin):
    '''
    The function return the dataframe with marked stages of a putt
    '''

    df = DetectPuttPoints(df, lower_bound_AZ, window, margin)
    df = df.reset_index()

    # Fill placeholder for the stage
    df['Stage'] = np.nan

    df.loc[df.Mark == 1, 'Stage'] = 'Back'
    df.loc[(df.Mark == 2) | (df.Mark == 3), 'Stage'] = 'Forward'

    # Check that there is something to return
    if df.loc[(df["Stage"] == 'Back') | (df["Stage"] == 'Forward'), :].shape[0] < 3:
        return (pd.DataFrame())

    else:
        # Get the first marked observation
        first_ind = df.Mark.first_valid_index()
        last_ind = df.Mark.last_valid_index()

        # Keep only relevant observations
        df = df.iloc[first_ind:(last_ind + 1), :]

        # Find end of the putt
        for i in range(1, df.shape[0]):
            if (df.iloc[i - 1, :]['Mark'] == 3) & (pd.isna(df.iloc[i, :]['Mark'])):

                df.iloc[i, df.columns.get_loc('Stage')] = 'Rest'

        df.Stage = df.Stage.ffill()

        # Clean up weird observations

        df.Stage.loc[(df.Stage.shift() == 'Rest') & (
            df.Stage.shift(-1) == 'Rest') & (df.Stage != 'Rest')] = 'Rest'

        return df


# Function to create dataframe
def SeparateDF(df, lower_bound_AZ, window, margin):
    '''
    We take the full data frame and create a disctionary with separate putts
    '''

    # Get stages
    df = MarkPutts(df, lower_bound_AZ, window, margin)

    pid = 1
    df['Id'] = pid

    for i in range(1, df.shape[0]):

        if (df.iloc[i, :]['Stage'] == 'Back') | (df.iloc[i, :]['Stage'] == 'Forward'):
            df.iloc[i, df.columns.get_loc('Id')] = pid

        elif (df.iloc[i, :]['Stage'] == 'Rest') & (df.iloc[i - 1, :]['Stage'] != 'Rest'):
            pid += 1  # Next move
            df.iloc[i, df.columns.get_loc('Id')] = np.nan

        else:
            df.iloc[i, df.columns.get_loc('Id')] = np.nan

    return df


# Custom class to make feature dataframe

# Function to calculate variables
# Function to calculate variables

def CalcVar(x, ts):
    '''
    Calculates variables based on Series of observations (x) and timestampts (ts). Returns Dictionary.

    '''

    Max = np.max(x)
    Min = np.min(x)
    Range = Max - Min
    Av = np.mean(x)
    StDev = np.std(x)

    AvDem = np.mean(x - Min)
    StDevDem = np.std(x - Min)

    Last = x[-1]

    Deriv = (x[-1] - x[0]) / (ts[-1] - ts[0])

    out = pd.Series({"Range": Range, "Max": Max, "Min": Min, "Last": Last, "Mean": Av, "StDev": StDev,
                     "MeanD": AvDem, "StDevDem": StDevDem, 'Deriv': Deriv})

    return out


class Putt:
    def __init__(self, df, lower_bound_AZ, window, margin):
        self.df = df
        self.lower_bound_AZ = lower_bound_AZ
        self.window = window
        self.margin = margin

    def marked(self):
        with pd.option_context('mode.chained_assignment', None):
            tmp_ = SeparateDF(self.df, self.lower_bound_AZ,
                              self.window, self.margin)

        # Check that there is something to return
        if tmp_.shape[0] > 0:
            tmp_ = tmp_.loc[tmp_.Stage != 'Rest', :]
            return(tmp_)

        else:
            return(pd.DataFrame())

    def features(self):
        df = self.marked()
        if df.shape[0] == 0:
            return (pd.DataFrame())

        else:
            # We keep only first put
            df = df.loc[(df.Id == 1) & (df.Stage == 'Forward'), :]

            # Commented out - excluded from the model
            # # Create vector distance
            # df['Accel'] = df[['AZ', 'AY', 'AX']].apply(lambda x: np.sqrt(
            #     x.iloc[0]**2 + x.iloc[1]**2 + x.iloc[2]**2), axis=1)
            # df['Gyro'] = df[['GZ', 'GY', 'GX']].apply(lambda x: np.sqrt(
            #     x.iloc[0]**2 + x.iloc[1]**2 + x.iloc[2]**2), axis=1)

            # Set variables
            # var_list = ['AX', 'AY', 'AZ', 'GX', 'GY', 'GZ', 'Accel', 'Gyro'] # X -axis exluded from the model
            #df = df.drop(['AX', 'GX'], axis=1, inplace=True)

            var_list = ['AY', 'AZ', 'GY', 'GZ']

            out = pd.DataFrame({"Id": 1}, index=[1])

            for v in var_list:
                tmp_ = df[[v, 'Time']].copy()

                t_ = CalcVar(tmp_[v].values, tmp_['Time'].values)
                t_.index = [v + "_" + sub for sub in t_.index.values]

                t_ = pd.DataFrame(t_).transpose()
                t_['Id'] = 1

                out = out.merge(t_, on='Id', how='left')

            return(out)

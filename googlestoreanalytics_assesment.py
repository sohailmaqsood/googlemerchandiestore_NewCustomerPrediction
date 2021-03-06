# -*- coding: utf-8 -*-
"""GoogleStoreAnalytics_Assesment

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1-2k1EGZ80EJZXSsexS4UxA1YjLKPpfRJ
"""

#importing libraries
import pandas as pd
import numpy as np

#for handling POSIX time column
from datetime import datetime as dt

import warnings
warnings.filterwarnings('ignore')

#model
from sklearn.tree import DecisionTreeClassifier

#used for measuring performanc of model
from sklearn.metrics import f1_score
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score

#lets load the data in dataframe
train = pd.read_csv('/content/drive/MyDrive/Colab Notebooks/Merkle_Google Store Analytics/sample_user_data.csv')

train.info()

#any customer having transaction greater than 0
#can be considered having made purchase
#we will use this to train model

train['purchased'] = train.transactions.notnull().astype(int)

#filling null values in bouces as 0, meaning session didn't bounced
train['bounces'].fillna(0,inplace=True)

#totaltransactionRevenue and transactions features are not of use since, we are predicting for new customers
#not for already logged customer.Also Visitor ID is of no use for our model. So dropping these
train.drop(['totalTransactionRevenue','transactions','fullVisitorId'],axis=1,inplace=True)

#since we need to make prediction only for new customers, we will filter our dataset for customers having VisitNumber as 1
train = train[train.VisitNumber == 1]
train.drop(['VisitNumber'],axis=1,inplace=True)

display(train.purchased.value_counts(normalize=True).plot.pie(title='Class Distribution',legend=True))
display(train.purchased.value_counts(normalize=True))

"""Data is highly imbalance. Number of people who made purchase is very Low"""

#converting datetime from time 
train['DateTime'] = train.VisitStartTime.apply(lambda tim:dt.fromtimestamp(tim).strftime('%Y-%m-%d %H'))
train.drop(['Date','VisitStartTime'],axis=1,inplace=True)

#extracting date and time from new column
train['Date'] = train.DateTime.str.slice(stop=9)
train['time'] = train.DateTime.str.slice(start=11)
train.drop(['DateTime'],axis=1,inplace=True)

citycross = pd.crosstab(train['city'],train['purchased'])

citycross.sort_values(by=1,ascending=False)

#there are two ways I think of using city column, either clubbing top cities as one entity in new columns and others as other
#but because most of these values are missing and can't be imputed, we will drop this column

train.drop(['city'],axis=1,inplace=True)

#relation between bounces and purchased
#Assumption is whenever session bounces, there is no purchase made
a = pd.crosstab(train.bounces,train.purchased)
a

"""As expected, any bounced session, doesn't have a purchase made"""

train.drop(['bounces'],axis=1,inplace=True)

#lets check for source column
src = pd.crosstab(train.source,train.purchased)
src.sort_values(by=1,ascending=False)

#lets convert source column into direct and indirect (anything other than direct)
train['source_direct'] = train.source.apply(lambda src:1 if src=='(direct)' else 0)

train.drop(['source'],axis=1,inplace=True)

#let check medium column
display(train.medium.value_counts())

mdm = pd.crosstab(train.medium,train.purchased)
print('----------------------------------------------')
display(mdm.sort_values(ascending=False,by=1))

"""Medium has 21 values as not set. We will replace these with 'Organic', since it has highest count after 'none'"""

train.medium.replace(to_replace='(not set)',value='organic',inplace=True)

#next is campaign
camp = pd.crosstab(train.campaign,train.purchased)
camp.sort_values(ascending=False,by=1)

"""not set values are so many that these rows cannot be even deleted. Plus most of the purchase made were for not set values, hence it seems like this column does not have much effect on the model. Hence we will not use this column in our model"""

train.deviceCategory.value_counts()

"""This column looks good. It does not have not set or missing values"""

train.mobileDeviceModel.value_counts()

"""Not device information is availablle in dataset. hence we will drop this column while training the model"""

train.ChannelGrouping.value_counts()

"""This also looks good and can be encoded"""

train.info()

#lets divide time into morning,afternoon,evening,night 
def timoday(x):
  x = int(x)
  if (x >= 18 and x <= 23) or (x >= 00 and x < 6):
    return 'Night'
  elif x >= 6 and x < 12:
    return 'Morning'
  elif x >= 12 and x < 18:
    return 'Noon-Eve'

train['timeoday'] = train.time.apply(lambda a:timoday(a))
train.drop(['time'],inplace=True,axis=1)

timecross = pd.crosstab(train.timeoday,train.purchased)
timecross

"""Night time has highest number of purchase made"""

#imputing the missing values in Time On Site column with Mean
from sklearn.impute import SimpleImputer
impt = SimpleImputer(missing_values=np.nan,strategy='mean')
train.timeOnSite = impt.fit_transform(train[['timeOnSite']])
train.pageviews = impt.fit_transform(train[['pageviews']])

train.drop(['campaign','mobileDeviceModel','Date'],axis=1,inplace=True)

train = pd.get_dummies(train,drop_first=True)

train.info()

from sklearn.model_selection import train_test_split
y = train['purchased']
x = train.drop(['purchased'],axis=1)
x_train,x_val,y_train,y_val = train_test_split(x,y,test_size=0.3)

#we will use Kfold validation to validate the model
f1 = np.array([])
acc = np.array([])
prec = np.array([])
recal = np.array([])

from sklearn.model_selection import StratifiedKFold
skf = StratifiedKFold(n_splits=5,random_state=42,shuffle=True)

for train_index,test_index in skf.split(x,y):
  x_train,x_test = x.iloc[train_index],x.iloc[test_index]
  y_train,y_test = y.iloc[train_index],y.iloc[test_index]
  model = DecisionTreeClassifier(random_state=42)
  model.fit(x_train,y_train)
  pred = model.predict(x_test)
  #print('{} iteration for decision tree has \n f1 score of {} \n accuracy of {} \n precision of {} \n recall of {}'.format(i,f1_score(y_test,pred),accuracy_score(y_test,pred),precision_score(y_test,pred),recall_score(y_test,pred)))
  f1 = np.append(f1,f1_score(y_test,pred))
  acc = np.append(acc,accuracy_score(y_test,pred))
  prec = np.append(prec,precision_score(y_test,pred))
  recal = np.append(recal,recall_score(y_test,pred))
  #print(f1_score(y_test,pred))
print('Mean of  \n F1 Score is {} \n Accuracy Score is {} \n Precision Score is {} \n Recall Score is {}'.format(np.mean(f1),np.mean(acc),np.mean(prec),np.mean(recal)))

"""Accuracy is very high but f1 score and other metrics are very low."""

#lets try parameter tuning using Gridsearch
parameters = {"criterion":["gini","entropy"],
              "splitter":["best","random"],
              "class_weight":[{1:50000,0:1},{1:100,0:1},{1:10000,0:1},{1:350782,0:2474}],
              "max_features":['auto','log2','sqrt',None]}

from sklearn.model_selection import GridSearchCV
tuning_model = GridSearchCV(model,param_grid=parameters,verbose=0,scoring='f1',cv=3)
tuning_model.fit(x,y)

#best hyperparameters
tuning_model.best_params_

#we will use Kfold validation to validate the model

f1 = np.array([])
acc = np.array([])
prec = np.array([])
recal = np.array([])

from sklearn.model_selection import StratifiedKFold
skf = StratifiedKFold(n_splits=5,random_state=42,shuffle=True)

for train_index,test_index in skf.split(x,y):
  x_train,x_test = x.iloc[train_index],x.iloc[test_index]
  y_train,y_test = y.iloc[train_index],y.iloc[test_index]
  model = DecisionTreeClassifier(random_state=42,criterion='entropy',max_features='auto',splitter='best',class_weight={0: 2474, 1: 350782})
  model.fit(x_train,y_train)
  pred = model.predict(x_test)
  #print('{} iteration for decision tree has \n f1 score of {} \n accuracy of {} \n precision of {} \n recall of {}'.format(i,f1_score(y_test,pred),accuracy_score(y_test,pred),precision_score(y_test,pred),recall_score(y_test,pred)))
  f1 = np.append(f1,f1_score(y_test,pred))
  acc = np.append(acc,accuracy_score(y_test,pred))
  prec = np.append(prec,precision_score(y_test,pred))
  recal = np.append(recal,recall_score(y_test,pred))
  #print(f1_score(y_test,pred))
print('Mean of  \n F1 Score is {} \n Accuracy Score is {} \n Precision Score is {} \n Recall Score is {}'.format(np.mean(f1),np.mean(acc),np.mean(prec),np.mean(recal)))

"""These scores are slightly better than what we had previously

Since our goal is to get rightly target more of those who are going to make purchase, lets try synthetic over sampling of set as well
"""

from imblearn.over_sampling import SMOTE
oversampler = SMOTE()
x,y = oversampler.fit_resample(x,y)

#we will use Kfold validation to validate the model

from sklearn.metrics import f1_score
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
f1 = np.array([])
acc = np.array([])
prec = np.array([])
recal = np.array([])

from sklearn.model_selection import StratifiedKFold
skf = StratifiedKFold(n_splits=5,random_state=42,shuffle=True)

for train_index,test_index in skf.split(x,y):
  x_train,x_test = x[train_index],x[test_index]
  y_train,y_test = y[train_index],y[test_index]
  model = DecisionTreeClassifier(random_state=42,criterion='entropy',max_features='auto',splitter='best',class_weight={0: 2474, 1: 350782}) #with Class Weights
  model.fit(x_train,y_train)
  pred = model.predict(x_test)
  #print('{} iteration for decision tree has \n f1 score of {} \n accuracy of {} \n precision of {} \n recall of {}'.format(i,f1_score(y_test,pred),accuracy_score(y_test,pred),precision_score(y_test,pred),recall_score(y_test,pred)))
  f1 = np.append(f1,f1_score(y_test,pred))
  acc = np.append(acc,accuracy_score(y_test,pred))
  prec = np.append(prec,precision_score(y_test,pred))
  recal = np.append(recal,recall_score(y_test,pred))
  #print(f1_score(y_test,pred))
print('Mean of  \n F1 Score is {} \n Accuracy Score is {} \n Precision Score is {} \n Recall Score is {}'.format(np.mean(f1),np.mean(acc),np.mean(prec),np.mean(recal)))

#we will use Kfold validation to validate the model

from sklearn.metrics import f1_score
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
f1 = np.array([])
acc = np.array([])
prec = np.array([])
recal = np.array([])

from sklearn.model_selection import StratifiedKFold
skf = StratifiedKFold(n_splits=5,random_state=42,shuffle=True)

for train_index,test_index in skf.split(x,y):
  x_train,x_test = x[train_index],x[test_index]
  y_train,y_test = y[train_index],y[test_index]
  model = DecisionTreeClassifier(random_state=42,criterion='entropy',max_features='auto',splitter='best') #without Class Weights
  model.fit(x_train,y_train)
  pred = model.predict(x_test)
  #print('{} iteration for decision tree has \n f1 score of {} \n accuracy of {} \n precision of {} \n recall of {}'.format(i,f1_score(y_test,pred),accuracy_score(y_test,pred),precision_score(y_test,pred),recall_score(y_test,pred)))
  f1 = np.append(f1,f1_score(y_test,pred))
  acc = np.append(acc,accuracy_score(y_test,pred))
  prec = np.append(prec,precision_score(y_test,pred))
  recal = np.append(recal,recall_score(y_test,pred))
  #print(f1_score(y_test,pred))
print('Mean of  \n F1 Score is {} \n Accuracy Score is {} \n Precision Score is {} \n Recall Score is {}'.format(np.mean(f1),np.mean(acc),np.mean(prec),np.mean(recal)))

"""***So if we Oversample over minority class, and bring in all the parameters, we tends to get high accuracy, percision and F1 Score. Hence we will create our Decision tree model on oversampled set and using the same parameters***"""

model = DecisionTreeClassifier(random_state=42,criterion='entropy',max_features='auto',splitter='best',class_weight={0: 2474, 1: 350782})
model.fit(x,y)

model.predict() #can be used to make prediction of any new customers on site
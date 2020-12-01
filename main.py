'''
Created by Dylan Gaines


'''

import pymongo
import csv
import json
import uuid
import time
import numpy as np

from pymongo import MongoClient


def setup_the_database():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["NBASalaryDatabase"]
    NBASalaries19to20 = mydb["PlayerSalaries2019-2020"]
    salary_loc = '/Users/dylan/PycharmProjects/NBAValueProject/newplayersalaries2019_2020.json'
    with open(salary_loc) as f:
        salary_data = json.load(f)
    for player in salary_data:
        player['Name'] = player['Name']
        player['Team'] = player['Team']
        player['Salary'] = int(player['Salary'])
        player['Rookie Scale Contract?'] = player['Rookie Scale Contract?']
        player['VORP'] = int(player['VORP'])
        player['Adjusted_VORP'] = int(player['Adjusted_VORP'])
        player['Win Shares'] = int(player['Win Shares'])
        player['Adjusted Win Shares'] = int(player['Adjusted Win Shares'])
        NBASalaries19to20.insert_one(player)
    print(myclient.list_database_names())
    print(mydb.list_collection_names())

def clear_the_collection():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["NBASalaryDatabase"]
    NBASalaries19to20 = mydb["PlayerSalaries2019-2020"]
    NBASalaries19to20.drop()

def test_query():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["NBASalaryDatabase"]
    NBASalaries19to20 = mydb["PlayerSalaries2019-2020"]

    salary_agg = [
        {'$match': {'Name': "Jaylen Brown"}},
        #'$project': {'_id': 0, 'summary': 0, 'slide_id': 0, 'slide_file': 0}},
        #{'$unwind': '$tiles'},
        #{'$project': {'tiles.tp': 1, 'tiles.s': 1, 'tiles.tn': 1}},
    ]

    the_result = NBASalaries19to20.aggregate(salary_agg)

    for answer in the_result:
        print(answer)

def rank_players(min_salary, rookies, avd_metrics, adj_metrics):

    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["NBASalaryDatabase"]
    NBASalaries19to20 = mydb["PlayerSalaries2019-2020"]

    name_list = []
    vorp_val_list = []
    win_shares_val_list = []

    if ',' in str(min_salary):
        min_salary = min_salary.replace(',', '')

    min_salary = int(min_salary)

    if adj_metrics == "Adjusted":
        if rookies == "Yes":
            salary_agg = [
                {'$project': {'_id': 0, 'Team': 0, 'VORP': 0, 'Win Shares': 0}},
                {'$match': {'Salary': {'$gte': min_salary}}}
            ]
        else:
            salary_agg = [
                {'$project': {'_id': 0, 'Team': 0, 'VORP': 0, 'Win Shares': 0}},
                {'$match': {'Rookie Scale Contract?': "No"}},
                {'$match': {'Salary': {'$gte': min_salary}}}
            ]

        the_result = NBASalaries19to20.aggregate(salary_agg)

        for answer in the_result:
            name_list.append(answer['Name'])
            div_VORP = answer['Adjusted_VORP'] / answer['Salary']
            div_Shares = answer['Adjusted Win Shares'] / answer['Salary']
            vorp_val_list.append(div_VORP)
            win_shares_val_list.append(div_Shares)

    else:
        if rookies == "Yes":
            salary_agg = [
                {'$project': {'_id': 0, 'Team': 0, 'Adjusted_VORP': 0, 'Adjusted Win Shares': 0}},
                {'$match': {'Salary': {'$gte': min_salary}}}
            ]
        else:
            salary_agg = [
                {'$project': {'_id': 0, 'Team': 0, 'Adjusted_VORP': 0, 'Adjusted Win Shares': 0}},
                {'$match': {'Rookie Scale Contract?': "No"}},
                {'$match': {'Salary': {'$gte': min_salary}}}
            ]

        the_result = NBASalaries19to20.aggregate(salary_agg)

        for answer in the_result:
            name_list.append(answer['Name'])
            div_VORP = answer['VORP'] / answer['Salary']
            div_Shares = answer['Win Shares'] / answer['Salary']
            vorp_val_list.append(div_VORP)
            win_shares_val_list.append(div_Shares)

    vorp_val_list = np.array(vorp_val_list)
    win_shares_val_list = np.array(win_shares_val_list)

    vorp_val_list = np.interp(vorp_val_list, (vorp_val_list.min(), vorp_val_list.max()), (0, +1000))
    win_shares_val_list = np.interp(win_shares_val_list, (win_shares_val_list.min(), win_shares_val_list.max()), (0, +1000))

    tot_dict = {}

    for counter, key in enumerate(name_list):
        vp_rank = vorp_val_list[counter]
        ws_rank = win_shares_val_list[counter]
        if avd_metrics == "VORP":
            ws_rank = 0
        elif avd_metrics == "Win Shares":
            vp_rank = 0
        tot_dict[key] = vp_rank + ws_rank

    sorted_dict = sorted(tot_dict.items(), key=lambda x: x[1], reverse=True)

    rank = 1

    for x in sorted_dict:
        print(rank,": ", x[0], ": ", (x[1]/10))
        rank = rank + 1

def Custom_or_Default():
    choice = input("Would you like to use the default criteria or would you like to customize your results? "
                   "(Respond with Default or Customize):\n")
    if choice != "Customize" and choice != "Default":
        print("Please enter a valid response")
        Custom_or_Default()
    else:
        return choice

def Get_Rookies():
    rookies = input("Would you like to include rookie contracts?" " Input Yes or No:\n")
    if rookies != "Yes" and rookies != "No" and rookies != "yes" and rookies != "no":
        print("Please enter a valid response")
        Get_Rookies()
    if rookies == "yes":
        rookies = "Yes"
    if rookies == "no":
        rookies = "No"
    else:
        return rookies

def Get_Advanced():
    avd = input("Would you like to use VORP, Win Shares, or Both? Input one of these three options:\n")
    if avd != "VORP" and avd != "Win Shares" and avd != "Both" and avd != "vorp" and avd != "Vorp" \
            and avd != "win shares" and avd != "both":
        print("Please enter a valid response")
        Get_Advanced()
    if avd == "vorp" or avd == "Vorp":
        avd = "VORP"
    if avd == "win shares":
        avd = "Win Shares"
    if avd == "both":
        avd == "Both"
    else:
        return rookies

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    #setup_the_database()
    #clear_the_collection()
    #test_query()
    print("Hello and welcome to the NBA Contract Value Ranker. This program will rank the value of NBA player contracts "
          "based on advanced metrics and user defined criteria.")
    choice = Custom_or_Default()
    if choice == "Default":
        min_salary = 5000000
        rookies = "No"
        avd_metrics = "Both"
        adj_metrics = "Adjusted"
    else:
        min_salary = input("What is the minimum salary you would like to rank?"
                           " Enter in 1 to return all applicable contracts:\n")
        rookies = Get_Rookies()
        avd_metrics = Get_Advanced()
        adj_metrics = input("Would you like to use my Adjusted advanced values or the Raw values? Input Adjusted or Raw:\n")
        print("\n")
    rank_players(min_salary, rookies, avd_metrics, adj_metrics)



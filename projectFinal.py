import sqlite3
import random, re
import pandas as pd

conn = sqlite3.connect("soccer_data/database.sqlite")

#########################################################################################
#########################################################################################


leagues = {
    1: (1729, "England Premier League"),
    2: (21518, "Spain LIGA BBVA"),
    3: (10257, "Italy Serie A"),
    4: (7809, "Germany 1. Bundesliga"),
    5: (4769, "France Ligue 1")
}

#########################################################################################
#########################################################################################
class Player:
    def __init__(self, name, id, rating):
        self.name = name
        self.id = id
        self.rating = rating


class Team:
    def __init__(self, name, rating, id):
        self.name = name
        self.id = id
        self.rating = rating
        self.roster = []
        self.points = 0
        self.budget = 0
        self.moneyearned = 0

    def determine_budget(self):
        if self.rating == 0:
            self.rating = get_team_ratings(self)
        budget = 25 * (10.74 * (1.204) ** self.rating)
        self.budget = budget

    def add_players(self, roster):
        for player_id in roster:
            name, rating = roster[player_id]
            player = Player(name, player_id, rating)
            self.roster.append(player)

    def play_match_versus(self, opponent):
        n = 0
        opponentGoals = 0
        MainTeamGoals = 0
        while n != 6:
            opponentScoreProb = opponent.rating
            MainTeamScoringProb = self.rating
            noGoalProb = 50

            outcomes = ['MainGoal', 'oppGoal', 'NoGoal']
            probability = [MainTeamScoringProb, opponentScoreProb, noGoalProb]
            result = random.choices(outcomes, weights=probability, k=1)[0]

            n += 1

            if result == 'MainGoal':
                MainTeamGoals += 1
            elif result == 'oppGoal':
                opponentGoals += 1

        if MainTeamGoals > opponentGoals:
            print('Win!')
            MainTeam.points += 3
        elif opponentGoals > MainTeamGoals:
            print("Loss..")
            opponent.points += 3
        else:
            print("Draw.")
            MainTeam.points += 1
            opponent.points += 1
        print(f'Score: {MainTeamGoals} - {opponentGoals}')


class League:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.teamRoster = []

    def add_teams(self, teamRoster, rating):
        for team_id in teamRoster:
            team = Team(teamRoster[team_id], rating, team_id)

            self.teamRoster.append(team)

#########################################################################################
#########################################################################################

def select_team(teams):
    choice = int(input("Enter the number of the team you want to select: "))
    return teams[choice]


def getLeague():
    while True:
        choice = int(input("Select a League (enter a number from the list above): "))
        print()
        if choice in leagues:
            league_id, name = leagues[choice]
            return league_id, name
        else:
            print(f'Error: {choice} is an invalid input. Please try again\n(for example to select the English Premier League, only input "1".')

def getYear():
    while True:
        desiredYear = input('What year would you like to simulate?\nSeasons availabe: 2008/2009 - 2015/2016\nInput the years seperated by a "/"\nExample Input: "2011/2012"\n\nInput a year: ')
        match = re.fullmatch(rf'20(\d\d)/20(\d\d)', desiredYear)
        if match:
            year1 = int(match.group(1))
            year2 = int(match.group(2))
            if year1 >= 8 and year2 <= 16 and year1 < year2:
                return desiredYear
            else:
                print(f'{desiredYear} is an invalid input')

def getClub(leagueid, league_name, year):
    print(f'Here are the clubs from the {league_name}:\n')
    league_print = pd.read_sql(
        f"SELECT DISTINCT team_long_name, team_api_id "
        f"FROM Team JOIN Match ON Team.team_api_id = Match.home_team_api_id "
        f"WHERE Match.league_id = {leagueid} AND season = '{year}'",
        conn)
    league = dict(zip(league_print['team_api_id'], league_print['team_long_name']))
    count = 1
    for club_id in league:
        print(f'{count}. {league[club_id]}')
        count += 1
    print('\n')
    while True:
        club_chosen = int(input(f'Please chose a club (chose by number): '))
        print()
        try:
            int(club_chosen)
        except:
            print('Invalid Input: Please input a number')
        count = 0
        for team_id in league:
            count += 1
            if count == club_chosen:
                team = league[team_id]
                print(f'Club selected {team}')
                return team, team_id, league, league_name, leagueid, year
        if club_chosen > len(league) or club_chosen < 1:
            print('Invalid Input: Please chose a number from the list above (ex: to chose West Ham, the valid input would be "4")')

def get_league_and_club():
    year = getYear()
    print("""        1. English Premier League
        2. Spanish La Liga
        3. Italian Serie A
        4. German Bundesliga
        5. French Ligue 1""")
    league_id, name = getLeague()
    print(f'League Selected: {name}')
    clubName, clubID, league, league_name, leagueid, year = getClub(league_id, name, year)

    return clubName, clubID, league, league_name, leagueid, year

def getRoster(clubName, clubID, league, year):
    roster = pd.DataFrame()
    count = 1
    while not count == 11:
        roster_item = pd.read_sql(f"""SELECT p.player_name, p.player_api_id, MAX(overall_rating) AS overall_rating
                FROM Player AS p
                JOIN Match AS m ON p.player_api_id = m.home_player_{count}
                JOIN Player_Attributes as pa ON p.player_api_id = pa.player_api_id
                WHERE m.home_team_api_id = {clubID} AND season = '{year}'
                GROUP BY p.player_name, p.player_api_id""", conn)
        count += 1
        roster = pd.concat([roster, roster_item])
    rosterDict = {
    row['player_api_id']: [row['player_name'], row['overall_rating']]
    for i, row in roster.iterrows()
    }
    return rosterDict

def displayRoster(clubName, clubID, league, year):
    roster = getRoster(clubName, clubID, league, year)
    count = 1
    for player_id in roster:
        print(f'{count}. {roster[player_id][0]} - Rating: {roster[player_id][1]}')
        count += 1
    return roster

def requestRoster(clubName, clubID, league, year):
    while True:
        response = input(f'Would you like to view the roster of {clubName}? (Y/N): ')
        if response.lower() == 'y' or response.lower() == 'yes':
            print(f"Displaying roster of {clubName}...")
            print()
            roster = displayRoster(clubName, clubID, league, year)
            return roster
        elif response.lower() == 'n' or response.lower() == 'no':
            roster = getRoster(clubName, clubID, league, year)
            print('\nTime for the next step')
            return roster
        else:
            print('Invalid input. Please answer in Y/N or Yes/No')

def get_team_ratings(team):
    total = 0
    count = 1
    for player in team.roster:
            total += player.rating
            count += 1
    return total/count

def estimate_transfer_fee(rating):
    if rating < 40:
        return random.randint(1000, 5400)
    elif rating < 50:
        return random.randint(5400, 27000)
    elif rating < 60:
        return random.randint(27000, 81000)
    elif rating < 65:
        return random.randint(81000, 216000)
    elif rating < 70:
        return random.randint(216000, 1080000)
    elif rating < 75:
        return random.randint(1080000, 4300000)
    elif rating < 80:
        return random.randint(4300000, 13000000)
    elif rating < 83:
        return random.randint(13000000, 32400000)
    elif rating < 85:
        return random.randint(32400000, 64800000)
    elif rating < 87:
        return random.randint(64800000, 97200000)
    elif rating < 90:
        return random.randint(97200000, 151200000)
    elif rating < 92:
        return random.randint(162000000, 216000000)
    elif rating < 94:
        return random.randint(216000000, 324000000)
    elif rating == 94:
        return random.randint(324000000, 400000000)
    else:
        return None

def potentialTransfer(matchday):
    if (matchday < 5) or (24 > matchday > 18):
        probability = [.4, .6]
        outcomes = [False,True]
        result = random.choices(outcomes, weights=probability, k=1)[0]
        if result == True:
            print(f'TRANSFER REQUEST')

            #get league
            league = random.randint(1, 5)
            if league in leagues:
                league_id, league_name = leagues[league]
            else:
                return

            #get club
            clubsInLeague = pd.read_sql(
                f"SELECT DISTINCT team_long_name, team_api_id FROM Team "
                f"JOIN Match ON Team.team_api_id = Match.home_team_api_id "
                f"WHERE Match.league_id = {league_id} AND season = '{year}'",
                conn)
            clubDict = dict(zip(clubsInLeague['team_api_id'], clubsInLeague['team_long_name']))
            team_ids = list(clubDict.keys())
            random_index = random.randint(0, len(team_ids) - 1)
            random_team_id = team_ids[random_index]
            random_club_name = clubDict[random_team_id]
            team = Team(random_club_name, 0, random_team_id)

            print(f'The request for a transfer comes from {random_club_name} from the {league_name}')
            while True:
                viewReply = input('Would you like to view the request? (Y/N): ')
                if viewReply.lower() == 'y' or viewReply.lower() == 'yes':
                    player_num = random.randint(0,len(MainTeam.roster) - 1)
                    player = MainTeam.roster[player_num]
                    price = estimate_transfer_fee(player.rating)
                    print(f'\n{random_club_name} is requesting to purchase {player.name} for ${price}')
                    while True:
                        acceptance = input('\nWould you like to accept the request? (Y/N): ')
                        if acceptance.lower() == 'y' or acceptance.lower() == 'yes':
                            team.roster.append(player)
                            MainTeam.roster.remove(player)
                            MainTeam.moneyearned += price
                            print(f'Accepted!\n')
                            return
                        elif acceptance.lower() == 'n' or acceptance.lower() == 'no':
                            print("Declined\n")
                            return
                        else:
                            print('Invalid input. Please answer in Y/N or Yes/No')
                elif viewReply.lower() == 'n' or viewReply.lower() == 'no':
                    return
                else:
                    print('Invalid input. Please answer in Y/N or Yes/No')

def transferMarket(year):
    while True:
        transferRequest = input('Would you like to buy any players now? (Y/N): ')
        if transferRequest.lower() == 'y' or transferRequest.lower() == 'yes':
                    print("""1. English Premier League\n2. Spanish La Liga\n3. Italian Serie A\n4. German Bundesliga\n5. French Ligue 1""")
                    desiredLeagueID, desiredLeagueName = getLeague()
                    desiredTeam, desiredTeamID, desiredLeague, desiredLeagueName, desiredLeagueID, year = getClub(desiredLeagueID, desiredLeagueName, year)
                    roster = displayRoster(desiredLeagueName, desiredTeamID, desiredLeague, year)
                    while True:

                        playerInput = int(input('\nWhich player would you like to chose? (Pleas input a number based off the list above): '))
                        if isinstance(playerInput, int) and 0 < playerInput <= len(roster):
                            count = 1
                            for playerID in roster:
                                if count == playerInput:
                                    transferTeam = Team(desiredTeam,0, desiredTeamID)
                                    transferTeam.add_players(roster)
                                    transferPlayer = None
                                    for player in transferTeam.roster:
                                        if player.id == playerID:
                                            transferPlayer = player
                                    price = estimate_transfer_fee(transferPlayer.rating)
                                    proceedCheck = input(f'{transferTeam.name} is requesting ${price} for {transferPlayer.name}.\nWould you like to proceed? (Y/N): ')
                                    if proceedCheck.lower() == 'y' or proceedCheck.lower() == 'yes':
                                        MainTeam.roster.append(transferPlayer)
                                        transferTeam.roster.remove(transferPlayer)
                                        MainTeam.moneyearned -= price
                                        print('Accepted!')
                                        print(f'Leaving Transfer Marktet...\n')
                                        return
                                    elif proceedCheck.lower() == 'n' or proceedCheck.lower() == 'no':
                                        print(f'Leaving Transfer Market...\n')
                                        return
                                    else:
                                        print(f'Invalid Input. Please enter either "y" or "yes", or "n" or "no"')
                                else:
                                    count += 1
        elif transferRequest.lower() == 'n' or transferRequest.lower() == 'no':
            print(f'Leaving Transfer Market...\n')
            return
        else:
            print('Invalid Input. Please enter either "y" or "yes", or "n" or "no".')


if __name__ == '__main__':
    #introduction
    print(f'\n\nWelcome to the European Soccer Manager Simulator! This is how the game works:\n'
          f'You will be given the opportunity to manage any club in any of the top 5 leagues in European Football.\n'
          f'Doing so, you will be ran through a simulation of the season, playing each team in your league.\n'
          f'Based on your teams players and ratings, your games will be simulated. Additionally, you will have the\n'
          f'opportunity to participate in the Summer and Winter transfer window! Clubs may request to buy players\n'
          f'from your squad. Doing so may will inevitability effect the outcome of your matches. However you are also able\n'
          f'to buy players to help your squad. Best of luck!\n')
    while True:
        beginPrompt = input('Ready to begin? (Y/N): ')
        if beginPrompt.lower() == 'y' or beginPrompt.lower() == 'yes':
            break
        elif beginPrompt.lower() == 'n' or beginPrompt.lower() == 'no':
            exit()
        else:
            print('Invalid input. Please answer in Y/N or Yes/No')
    print()


    #user interface and selection of league and club
    clubName, clubID, league, league_name, leagueid, year = get_league_and_club()
    roster = requestRoster(clubName, clubID, league, year)

    #upload info to classes for the user's selected team
    MainTeam = Team(clubName, 0, clubID)
    MainTeam.add_players(roster)
    MainTeam.rating = get_team_ratings(MainTeam)
    MainTeam.determine_budget()
    MainLeague = League(league_name, leagueid)
    MainLeague.add_teams(league, rating=0)
    # MainLeague.update_league_ratings()

    #final display of user info before starting the season
    print(f'\n\n\nYour league: {MainLeague.name}\nYour team: {MainTeam.name}\nTeam Rating: {int(MainTeam.rating)}\nThis Year\'s Transfer Budget: ${MainTeam.budget:.2f}\n\nTime to start the season!\n')

    #open transfer window
    print('The transfer window is now open.\nIt will close after matchday 5 and open again between matchday 18 to 24.\nYou will now recieve transfer requests from other clubs for your players.\nYou now have the option to buy players of your own.\n')
    transferMarket(year)


    #begin simulation
    matchday = 1
    for opponent in MainLeague.teamRoster:
        if opponent.id != MainTeam.id:
            potentialTransfer(matchday)
            print(f'Matchday {matchday} of {(len(league)-1) * 2} is against: {opponent.name}')
            opponent.add_players(getRoster(opponent.name, opponent.id, opponent.name, year))
            opponent.rating = get_team_ratings(opponent)
            MainTeam.play_match_versus(opponent)
            print()
            matchday += 1
    for opponent in MainLeague.teamRoster:
        if opponent.id != MainTeam.id:
            print(f'Matchday {matchday} of {(len(league)-1) * 2} is against: {opponent.name}')
            opponent.add_players(getRoster(opponent.name, opponent.id, opponent.name, year))
            opponent.rating = get_team_ratings(opponent)
            MainTeam.play_match_versus(opponent)
            print()
            matchday += 1

    print(f'You finished the season with {MainTeam.points} points!')
    print(f'You earned the club an additional {MainTeam.moneyearned}')
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
    def __init__(self, name, defRating, offRating, rating, id):
        self.name = name
        self.id = id
        self.defRating = defRating
        self.offRating = offRating
        self.rating = rating
        self.roster = []
        self.points = 0
        self.budget = 0
        self.moneyearned = 0

    def determine_budget(self, year):
        if self.rating == 0:
            self.defRating, self.offRating, self.rating = get_team_ratings(self.id, year)

        # Base budget scale (in millions)
        BASE_BUDGET = 300_000

        # Growth of budget per team rating point
        GROWTH_RATE = 1.085  # about 8.5% per rating point

        # Exponential budget by team strength
        raw_budget = BASE_BUDGET * (GROWTH_RATE ** self.rating)

        self.budget = round(raw_budget / 1_000_000) * 1_000_000

    def add_players(self, roster):
        for player_id in roster:
            name, rating = roster[player_id]
            player = Player(name, player_id, rating)
            self.roster.append(player)

    def play_match_versus(self, opponent):
        # Match tempo (soft total)
        # Not fixed, but bounded so your league doesn't turn into chaos
        # (If you downloaded this off Github, fell free to edit your TOTAL_CHANCES)
        TOTAL_CHANCES = random.randint(12, 18)

        # Attack power: this is how strong the attack is which is based off the difference between offence and defence
        # How strongly ratings matter. 1.5–2.0 is usually a good range.
        # (If you downloaded this off Github, fell free to edit your alpha)
        alpha = 2
        main_power = (self.offRating / opponent.defRating) ** alpha
        opp_power = (opponent.offRating / self.defRating) ** alpha

        # with the amount of total chances calculated earlier, see how many go to each team based off power ratings
        main_share = main_power / (main_power + opp_power)
        main_chances = round(TOTAL_CHANCES * main_share)
        # This is so nobody ends up with 0 or only 1 chance
        main_chances = max(2, min(main_chances, TOTAL_CHANCES - 2))
        opp_chances = TOTAL_CHANCES - main_chances

        # Chance and goal conversion
        # Base chance quality. Tune this to control average goals per match.
        # (If you downloaded this off Github, fell free to edit your BASE_XG)
        BASE_XG = 0.25

        MainTeamGoals = 0
        opponentGoals = 0

        # Main team's goal chances (each attack)
        for chance in range(main_chances):
            # Stronger offense vs weaker defense means a higher conversion/goal on each chance
            xg = BASE_XG * (self.offRating / opponent.defRating)

            # Cap that to prevent arcade scorelines if ratings get extreme
            xg = min(xg, 0.35)
            if random.random() < xg:
                MainTeamGoals += 1

        # Opponent attacking chances
        for chance in range(opp_chances):
            xg = BASE_XG * (opponent.offRating / self.defRating)
            xg = min(xg, 0.30)

            if random.random() < xg:
                opponentGoals += 1

        # Result + points
        if MainTeamGoals > opponentGoals:
            print('Win!')
            self.points += 3
        elif opponentGoals > MainTeamGoals:
            print("Loss..")
            opponent.points += 3
        else:
            print("Draw.")
            self.points += 1
            opponent.points += 1

        print(f'Score: {MainTeamGoals} - {opponentGoals}')


class League:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.teamRoster = []

    def add_teams(self, teamRoster, defRating, offRating, rating):
        for team_id in teamRoster:
            team = Team(teamRoster[team_id], defRating, offRating, rating, team_id)

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
            print(
                f'Error: {choice} is an invalid input. Please try again\n(for example to select the English Premier League, only input "1".')


def getYear():
    while True:
        desiredYear = input(
            'What year would you like to simulate?\nSeasons available: 2008/2009 - 2015/2016\nInput the years separated by a "/"\nExample Input: "2011/2012"\n\nInput a year: ')
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
        club_chosen = int(input(f'Please choose a club (choose by number): '))
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
            print(
                'Invalid Input: Please choose a number from the list above (ex: to choose West Ham, the valid input would be "4")')


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
    # Split '2014/2015' to get '2014' and '2015'
    start_year = year.split('/')[0]
    end_year = year.split('/')[1]

    # Construct the date strings for sql
    date_start = f"{start_year}-07-01"
    date_end = f"{end_year}-06-30"

    # sql to get roster
    query = f"""
    SELECT 
        hp.player_id, 
        p.player_name, 
        ROUND(AVG(pa.overall_rating), 2) AS avg_overall
    FROM Match m
    JOIN (
        SELECT match_api_id, home_player_1 AS player_id FROM Match
        UNION ALL SELECT match_api_id, home_player_2 FROM Match
        UNION ALL SELECT match_api_id, home_player_3 FROM Match
        UNION ALL SELECT match_api_id, home_player_4 FROM Match
        UNION ALL SELECT match_api_id, home_player_5 FROM Match
        UNION ALL SELECT match_api_id, home_player_6 FROM Match
        UNION ALL SELECT match_api_id, home_player_7 FROM Match
        UNION ALL SELECT match_api_id, home_player_8 FROM Match
        UNION ALL SELECT match_api_id, home_player_9 FROM Match
        UNION ALL SELECT match_api_id, home_player_10 FROM Match
        UNION ALL SELECT match_api_id, home_player_11 FROM Match
    ) hp ON hp.match_api_id = m.match_api_id
    JOIN Player p ON p.player_api_id = hp.player_id
    JOIN Player_Attributes pa ON pa.player_api_id = hp.player_id
    WHERE m.home_team_api_id = {clubID}
      AND m.season = '{year}'
      AND pa.date BETWEEN '{date_start}' AND '{date_end}'
    GROUP BY hp.player_id, p.player_name
    """

    roster = pd.read_sql(query, conn)

    rosterDict = {
        row['player_id']: [row['player_name'], row['avg_overall']]
        for _, row in roster.iterrows()
    }

    return rosterDict


def displayRoster(clubName, clubID, league, year):
    roster = getRoster(clubName, clubID, league, year)
    count = 1
    for player_id in roster:
        print(f'{count}. {roster[player_id][0]} - Rating: {int(round(roster[player_id][1], 0))}')
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


def get_team_ratings(clubID, year):
    # Handle date range based on the season string '2014/2015'
    start_year = year.split('/')[0]
    end_year = year.split('/')[1]
    date_start = f"{start_year}-07-01"
    date_end = f"{end_year}-06-30"

    # The SQL Query using CTEs
    query = f"""
        WITH lineup AS (
            SELECT m.home_team_api_id AS team_id, m.match_api_id, m.home_player_1 AS player_id, 1 AS slot FROM Match m
            UNION ALL SELECT m.home_team_api_id, m.match_api_id, m.home_player_2, 2 FROM Match m
            UNION ALL SELECT m.home_team_api_id, m.match_api_id, m.home_player_3, 3 FROM Match m
            UNION ALL SELECT m.home_team_api_id, m.match_api_id, m.home_player_4, 4 FROM Match m
            UNION ALL SELECT m.home_team_api_id, m.match_api_id, m.home_player_5, 5 FROM Match m
            UNION ALL SELECT m.home_team_api_id, m.match_api_id, m.home_player_6, 6 FROM Match m
            UNION ALL SELECT m.home_team_api_id, m.match_api_id, m.home_player_7, 7 FROM Match m
            UNION ALL SELECT m.home_team_api_id, m.match_api_id, m.home_player_8, 8 FROM Match m
            UNION ALL SELECT m.home_team_api_id, m.match_api_id, m.home_player_9, 9 FROM Match m
            UNION ALL SELECT m.home_team_api_id, m.match_api_id, m.home_player_10, 10 FROM Match m
            UNION ALL SELECT m.home_team_api_id, m.match_api_id, m.home_player_11, 11 FROM Match m
        ),
        player_metrics AS (
            SELECT
                l.team_id,
                l.player_id,
                ROUND((AVG(pa.crossing) + AVG(pa.finishing) + AVG(pa.penalties) + AVG(pa.dribbling) + AVG(pa.shot_power)) / 5.0, 2) AS avg_attack,
                ROUND(
                    CASE
                        WHEN l.slot = 1 THEN
                            (AVG(pa.gk_diving) + AVG(pa.gk_handling) + AVG(pa.gk_kicking) + AVG(pa.gk_positioning) + AVG(pa.gk_reflexes)) / 5.0
                        ELSE
                            (AVG(pa.aggression) + AVG(pa.interceptions) + AVG(pa.strength) + AVG(pa.marking) + AVG(pa.standing_tackle) + AVG(pa.sliding_tackle)) / 6.0
                    END
                , 2) AS avg_defence
            FROM lineup l
            JOIN Match m ON m.match_api_id = l.match_api_id
            JOIN Player_Attributes pa ON pa.player_api_id = l.player_id
            WHERE l.team_id = {clubID}
              AND pa.date BETWEEN '{date_start}' AND '{date_end}'
              AND l.player_id IS NOT NULL
            GROUP BY l.team_id, l.player_id, l.slot
        ),
        ranked AS (
            SELECT
                pm.*,
                ROW_NUMBER() OVER (ORDER BY avg_attack DESC)  AS atk_rank,
                ROW_NUMBER() OVER (ORDER BY avg_defence DESC) AS def_rank
            FROM player_metrics pm
        ),
        team_avgs AS (
            SELECT
                AVG(CASE WHEN atk_rank <= 3 THEN avg_attack  END) AS team_avg_attack,
                AVG(CASE WHEN def_rank <= 5 THEN avg_defence END) AS team_avg_defence
            FROM ranked
        )
        SELECT
            ROUND(team_avg_attack, 2) AS AvgAttack,
            ROUND(team_avg_defence, 2) AS AvgDefence,
            ROUND((ROUND(team_avg_attack, 2) + ROUND(team_avg_defence, 2)) / 2, 0) AS Rating
        FROM team_avgs;
        """

    # Execute and Return
    df = pd.read_sql(query, conn)

    res = df.iloc[0]
    return (res['AvgAttack'], res['AvgDefence'], res['Rating'])


def estimate_transfer_fee(rating):
    if rating < 40:
        low, high = 1_000, 5_400
    elif rating < 50:
        low, high = 5_400, 27_000
    elif rating < 60:
        low, high = 27_000, 81_000
    elif rating < 65:
        low, high = 81_000, 216_000
    elif rating < 70:
        low, high = 216_000, 1_080_000
    elif rating < 75:
        low, high = 1_080_000, 4_300_000
    elif rating < 80:
        low, high = 4_300_000, 13_000_000
    elif rating < 83:
        low, high = 13_000_000, 32_400_000
    elif rating < 85:
        low, high = 32_400_000, 64_800_000
    elif rating < 87:
        low, high = 64_800_000, 97_200_000
    elif rating < 90:
        low, high = 97_200_000, 151_200_000
    elif rating < 92:
        low, high = 151_200_000, 216_000_000
    elif rating < 94:
        low, high = 216_000_000, 300_000_000
    else:
        low, high = 300_000_000, 400_000_000

    fee = random.randint(low, high)

    # Round to nearest million
    fee = round(fee / 1_000_000) * 1_000_000

    # return the fee (or 1M as lowest option)
    return max(fee, 1_000_000)


def potentialTransfer(matchday):
    if (matchday < 5) or (24 > matchday > 18):
        probability = [.4, .6]
        outcomes = [False, True]
        result = random.choices(outcomes, weights=probability, k=1)[0]
        if result == True:
            print('TRANSFER REQUEST')

            # get league
            league = random.randint(1, 5)
            if league in leagues:
                league_id, league_name = leagues[league]
            else:
                return

            # get club
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
            team = Team(random_club_name, 0, 0, 0, random_team_id)

            print(f'The request for a transfer comes from {random_club_name} from the {league_name}')
            while True:
                viewReply = input('Would you like to view the request? (Y/N): ')
                if viewReply.lower() == 'y' or viewReply.lower() == 'yes':
                    player_num = random.randint(0, len(MainTeam.roster) - 1)
                    player = MainTeam.roster[player_num]
                    price = estimate_transfer_fee(player.rating)
                    print(f"\n{random_club_name} is requesting to purchase {player.name} for ${price:,.2f}")
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
                    print()
                    return
                else:
                    print('Invalid input. Please answer in Y/N or Yes/No')


def transferMarket(year):
    while True:
        transferRequest = input('Would you like to buy any players now? (Y/N): ')
        if transferRequest.lower() == 'y' or transferRequest.lower() == 'yes':
            print(
                """1. English Premier League\n2. Spanish La Liga\n3. Italian Serie A\n4. German Bundesliga\n5. French Ligue 1""")
            desiredLeagueID, desiredLeagueName = getLeague()
            desiredTeam, desiredTeamID, desiredLeague, desiredLeagueName, desiredLeagueID, year = getClub(
                desiredLeagueID, desiredLeagueName, year)
            roster = displayRoster(desiredLeagueName, desiredTeamID, desiredLeague, year)
            while True:

                playerInput = int(
                    input('\nWhich player would you like to choose? (Please input a number based on the list above): '))
                if isinstance(playerInput, int) and 0 < playerInput <= len(roster):
                    count = 1
                    for playerID in roster:
                        if count == playerInput:
                            transferTeam = Team(desiredTeam, 0, 0, 0, desiredTeamID)
                            transferTeam.add_players(roster)
                            transferPlayer = None
                            for player in transferTeam.roster:
                                if player.id == playerID:
                                    transferPlayer = player
                            price = estimate_transfer_fee(transferPlayer.rating)
                            proceedCheck = input(
                                f'{transferTeam.name} is requesting ${price:,.2f} for {transferPlayer.name}.\nWould you like to proceed? (Y/N): ')
                            if proceedCheck.lower() == 'y' or proceedCheck.lower() == 'yes':
                                MainTeam.roster.append(transferPlayer)
                                transferTeam.roster.remove(transferPlayer)
                                MainTeam.moneyearned -= price
                                print('Accepted!')
                                print(f'Leaving Transfer Market...\n')
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
    print(f'\n\nWelcome to the European Soccer Manager Simulator! This is how the simulator works:\n'
          f'You will be given the opportunity to manage any club in any of the top 5 leagues in European football.\n'
          f'In doing so, you will be run through a simulation of the season, playing each team in your league.\n'
          f'Based on your team’s players and ratings, your matches will be simulated. Additionally, you will have the\n'
          f'opportunity to participate in the Summer and Winter transfer windows. Clubs may request to buy players\n'
          f'from your squad. Doing so will inevitably affect the outcome of your matches. However, you are also able\n'
          f'to buy players to strengthen your squad. Best of luck!\n')

    while True:
        beginPrompt = input('Ready to begin? (Y/N): ')
        if beginPrompt.lower() == 'y' or beginPrompt.lower() == 'yes':
            break
        elif beginPrompt.lower() == 'n' or beginPrompt.lower() == 'no':
            exit()
        else:
            print('Invalid input. Please answer in Y/N or Yes/No')
    print()

    clubName, clubID, league, league_name, leagueid, year = get_league_and_club()
    roster = requestRoster(clubName, clubID, league, year)

    # upload info to classes for the user's selected team
    MainTeam = Team(clubName, 0, 0, 0, clubID)
    MainTeam.add_players(roster)
    MainTeam.defRating, MainTeam.offRating, MainTeam.rating = get_team_ratings(MainTeam.id, year)
    MainTeam.determine_budget(year)
    MainLeague = League(league_name, leagueid)
    MainLeague.add_teams(league, defRating=0, offRating=0, rating=0)
    # MainLeague.update_league_ratings()

    # final display of user info before starting the season
    print(f"""\n\n\n
    Your league: {MainLeague.name}
    Your team: {MainTeam.name}
    Team Overall Rating: {int(MainTeam.rating)}
    Team Offensive Rating: {int(MainTeam.offRating)}
    Team Defensive Rating: {int(MainTeam.defRating)}
    This Year's Transfer Budget: ${MainTeam.budget:,.2f}

    \nTime to start the season!\n
            """)

    # open transfer window
    print(
        'The transfer window is now open.\nIt will close after matchday 5 and open again between matchday 18 to 24.\nYou will now receive transfer requests from other clubs for your players.\nYou now have the option to buy players of your own.\n')
    transferMarket(year)

    # begin simulation
    matchday = 1

    for opponent in MainLeague.teamRoster:
        if opponent.id != MainTeam.id:
            potentialTransfer(matchday)
            print(f'Matchday {matchday} of {(len(league) - 1) * 2} is against: {opponent.name}')
            opponent.add_players(getRoster(opponent.name, opponent.id, opponent.name, year))
            opponent.defRating, opponent.offRating, opponent.rating = get_team_ratings(opponent.id, year)
            MainTeam.play_match_versus(opponent)
            print()
            matchday += 1
    for opponent in MainLeague.teamRoster:
        if opponent.id != MainTeam.id:
            print(f'Matchday {matchday} of {(len(league) - 1) * 2} is against: {opponent.name}')
            opponent.add_players(getRoster(opponent.name, opponent.id, opponent.name, year))
            opponent.rating = get_team_ratings(opponent.id, year)
            MainTeam.play_match_versus(opponent)
            print()
            matchday += 1

    print(f'You finished the season with {MainTeam.points} points!')

    net = MainTeam.moneyearned  # net transfer result
    remaining = MainTeam.budget + net  # budget left after transfers

    # Remaining budget
    print(f'Remaining transfer budget: ${remaining:,.0f}')
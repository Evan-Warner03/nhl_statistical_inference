import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service


def scrape_nhl_data(wd, outpath):
	team_names = ['New Jersey Devils', 'Pittsburgh Penguins', 'Ottawa Senators','Colorado Avalanche', 'Detroit Red Wings', 'Los Angeles Kings', 'New York Rangers', 'St. Louis Blues', 'Edmonton Oilers', 'Dallas Stars', 'Philadelphia Flyers', 'Vancouver Canucks', 'Washington Capitals', 'Toronto Maple Leafs', 'Boston Bruins', 'Buffalo Sabres', 'San Jose Sharks', 'Arizona Coyotes', 'Carolina Hurricanes', 'Winnipeg Jets', 'Chicago Blackhawks', 'Montreal Canadiens', 'Tampa Bay Lightning', 'Florida Panthers', 'Calgary Flames', 'Columbus Blue Jackets', 'Anaheim Ducks', 'Nashville Predators', 'New York Islanders', 'Minnesota Wild']

	skt_queries = []
	gk_queries = []
	seasons = range(2002, 2022)
	for year in seasons:
		# skater stats
		skt_queries.append('https://www.espn.com/nhl/stats/team/_/season/{}/seasontype/2'.format(year))
		# goalie stats
		gk_queries.append('https://www.espn.com/nhl/stats/team/_/view/goaltending/season/{}/seasontype/2'.format(year))

	f = open(outpath, 'w+')
	csv_writer = csv.writer(f)
	header = ['TEAM', 'GP', 'GF/G', 'A', 'PTS', 'PP%', 'SHG', 'S', 'S%', 'PIM', 'PK%', 'GA/G', 'W', 'L', 'OTL', 'SA', 'GA', 'S', 'SV%', 'SO']
	csv_writer.writerow(header)

	for i in range(len(skt_queries)):
		# retrieve the web page
		wd.get(skt_queries[i])

		# extract the skater stats
		teams = []
		skt_stats = []
		stats_table = wd.find_elements(By.XPATH, value='//tbody')[1]
		stats = stats_table.find_elements(By.XPATH, value='//tr')
		for s in stats:
			if s.text == 'RK\nTEAM':
				continue

			added = False
			for t in team_names:
				if t in s.text.replace('-\n', ''):
					added = True
					teams.append(s.text.replace('-\n', ''))

			if not added:
				if 'GP' not in s.text:
					skt_stats.append(s.text.split('\n'))

		# extract the goalie stats
		wd.get(gk_queries[i])
		teams2 = []
		gk_stats = []
		stats_table = wd.find_elements(By.XPATH, value='//tbody')[1]
		stats = stats_table.find_elements(By.XPATH, value='//tr')
		for s in stats:
			if s.text == 'RK\nTEAM':
				continue

			added = False
			for t in team_names:
				if t in s.text.replace('-\n', ''):
					added = True
					t1 = s.text.replace('-\n', '').split()
					t2 = ""
					for i in range(1, len(t1)):
						t2 += f'{t1[i]} '
					teams2.append(t2[:-1])

			if not added:
				if 'GP' not in s.text:
					gk_stats.append(s.text.split('\n'))

		# stitch skater and goalie stats together
		final_data = []
		for i in range(len(teams)):
			temp = [teams[i]]
			temp.extend(skt_stats[i][:-3])
			final_data.append(temp)

		gk_data = []
		for i in range(len(teams2)):
			temp = [teams2[i]]
			temp.extend(gk_stats[i][:-3])
			gk_data.append(temp)
		
		for i in range(len(final_data)):
			for ii in range(len(final_data)):
				if gk_data[i][0] == final_data[ii][0]:
					final_data[ii].extend(gk_data[i][1:-3])

		# final data columns:
		# TEAM GP GF/G A PTS PP% SHG S S% PIM PK% GA/G W L OTL SA GA S SV% SO
		# clean up final data, add team_pts% column
		for i in range(len(final_data)):
			final_data[i].pop(12)
			# 164 is the max number of points you can achieve in a season
			final_data[i].append((int(final_data[i][13])*2 + int(final_data[i][15])*2)/164)
			
			# remove commas
			for ii in range(len(final_data[i])):
				while ',' in str(final_data[i][ii]):
					final_data[i][ii] = final_data[i][ii].replace(',', '')

				if ' ' not in str(final_data[i][ii]):
					final_data[i][ii] = float(final_data[i][ii])

		
		for i in range(len(final_data)):
			csv_writer.writerow(final_data[i])

	wd.quit()



if __name__ == "__main__":
	s = Service('./chromedriver')
	wd = webdriver.Chrome(service=s)
	outpath = './scraped_nhl_data.csv'
	scrape_nhl_data(wd, outpath)
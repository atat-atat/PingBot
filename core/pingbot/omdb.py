"""
OMDb Parser
"""
from core import pingbot
from urllib.parse import quote

async def get_media_type(title):
	"""
	Returns the type of media based on the title.
	"""
	title = quote(title) #convert string

	url = "http://www.omdbapi.com/?t={}&y=&plot=short&r=json".format(title)
	resp = await pingbot.WT().async_json_content(url) #get JSON contents from URL

	if resp["Response"] == "False":
		return None

	return resp["Type"]

async def get_movie(title):
	"""
	Returns the movie class.
	"""
	title = quote(title) #convert string

	url = "http://www.omdbapi.com/?t={}&y=&plot=short&r=json".format(title)
	resp = await pingbot.WT().async_json_content(url) #get JSON contents from URL

	if resp["Response"] == "False": #check if response failed
		return None

	return Movie(resp["Title"], resp["Year"], resp["Rated"], resp["Released"], resp["Runtime"], resp["Genre"], resp["Director"], resp["Writer"], resp["Actors"], resp["Plot"], resp["Language"], resp["Country"], resp["Awards"], resp["Poster"], resp["Metascore"], resp["imdbRating"], resp["imdbVotes"], resp["imdbID"], resp["Type"], resp["Response"]) #return movie class

class Movie:
	def __init__(self, title, year, rated, released, runtime, genre, director, writer, actors, plot, language, country, awards, poster, metascore, imdb_rating, imdb_votes, imdb_id, media_type, response):
		self.title = title
		self.year = year
		self.rated = rated
		self.released = released
		self.runtime = runtime
		self.genre = genre
		self.director = director
		self.actors = actors
		self.plot = plot
		self.language = language
		self.country = country
		self.awards = awards
		self.poster = poster
		self.metascore = metascore
		self.imdb_rating = imdb_rating
		self.imdb_votes = imdb_votes
		self.imdb_id = imdb_id
		self.media_type = media_type
		self.response = response
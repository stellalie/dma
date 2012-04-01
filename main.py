import re
import math

class TestUser(object):
	users = {}
	track_no = ""
	
	def __init__(self, id, test_items):
		self.id = id
		self.test_items = test_items
		
	@classmethod
	def read_file(cls, filename):
		f = open(filename, "r")
		user_id = None
		test_items = {}
		for line in f:
			# the line contains item - score entry is None by default
			if not re.search('\\|', line):
				line = line.split('\t')
				item_id = int(line[0].strip())
				item_id_object = Item.find(item_id)
				item_score = None
				if track_no == "1": item_score = int(line[1].strip())
				#enable this to run training data as test on track 2
				#item_score = int(line[1].strip())
				test_items[item_id_object] = item_score

			# the line contains user id
			else:
				if user_id != None:
					cls.users[user_id] = cls(user_id, test_items)
					user_id = None
					test_items = {}
				line = line.split("|")
				user_id = int(line[0].strip())
		cls.users[user_id] = cls(user_id, test_items)
		f.close()

	@classmethod
	def get_predicted_score(cls, original_test_user, test_item):
		test_user = User.find(original_test_user.id)
		active_user_average_score = User.get_average_score_all_item_type(test_user)
		k = 0.1
		predicted_score = 0.0
		similarity_sum = 0.0
		
		#similar item averages on test item
		if track_no == "2":
			similar_items = Item.get_similar_items(test_item)
			average_rating_sum = 0
			rating_sum = 0
			count = 0
			for user_id, user in User.users.iteritems():
				for item, item_rating in user.rated_items.iteritems():
					if item in similar_items:
						rating_sum = rating_sum + item_rating
						count = count + 1
			if not count == 0: average_rating_sum = rating_sum / count
		
		#similarity balancer sum calculation on users who rate the test item
		for user_id, user in User.users.iteritems():
			similarity_score = User.get_similarity_score(user, test_user)
			similarity_sum_per_user = 0
			
			#only users who had similarity score < 0.8 to test user won't be considered
			if ((test_item in user.rated_items) & (similarity_score > 0.8)):
				a = user.rated_items[test_item]
				b = User.get_average_score_item_type(test_user, test_item.__class__)
				
				#if no past data, then calculation won't be considered
				if b == None: b = 0
				similarity_sum_per_user = similarity_score * (a - b)
			similarity_sum = similarity_sum + similarity_sum_per_user
		
		#score predicition calculation
		predicted_score = active_user_average_score + k * (similarity_sum)
		if track_no == "2":
			if not count == 0: predicted_score = (0.1 * predicted_score) + (0.9 * average_rating_sum)
		return predicted_score
	
	@classmethod
	def get_rmse_score(cls, real_score, predicted_score):
		return math.pow((real_score - predicted_score), 2)
		
class User(object):
	users = {}

	def __init__(self, id, rated_items):
		self.id = id
		self.rated_items = rated_items

	@classmethod
	def read_file(cls, filename):
		f = open(filename, "r")
		user_id = None
		rated_items = {}
		for line in f:
			# the line contains item - score entry
			if re.search('\t', line):
				line = line.split('\t')
				item_id = int(line[0].strip())
				item_id_object = Item.find(item_id)
				item_score = int(line[1].strip())
				rated_items[item_id_object] = item_score
			
			# the line contains user id
			else:
				if user_id != None:
					cls.users[user_id] = cls(user_id, rated_items)
					user_id = None
					rated_items = {}
				line = line.split("|")
				user_id = int(line[0].strip())
		cls.users[user_id] = cls(user_id, rated_items)
		f.close()
	
	@classmethod
	def find(cls, id):
		if cls == User:
			if id in User.users: return User.users[id]
			raise Exception("Warning: Item type is not listed.")
		else:
			return cls.users[id]
	
	@classmethod
	def get_classified_rated_items(cls, user):
		classified_rated_items = {}
		rated_items_artist = []
		rated_items_genre = []
		rated_items_album = []
		rated_items_track = []
		for item_id_object in user.rated_items:
			if isinstance(item_id_object, Artist): rated_items_artist.append(item_id_object)
			elif isinstance(item_id_object, Genre): rated_items_genre.append(item_id_object)
			elif isinstance(item_id_object, Album): rated_items_album.append(item_id_object)
			elif isinstance(item_id_object, Track): rated_items_track.append(item_id_object)
			else: print "Warning: Item type is not listed"
		classified_rated_items[Artist] = rated_items_artist
		classified_rated_items[Genre] = rated_items_genre
		classified_rated_items[Album] = rated_items_album
		classified_rated_items[Track] = rated_items_track
		return classified_rated_items
		
	@classmethod
	def get_coitems(cls, user1, user2):
		coitems = {}
		coitems_artist = []
		coitems_genre = []
		coitems_album = []
		coitems_track = []
		for item in user1.rated_items:
			if item in user2.rated_items:
				if isinstance(item, Artist): coitems_artist.append(item)
				elif isinstance(item, Genre): coitems_genre.append(item)
				elif isinstance(item, Album): coitems_album.append(item)
				elif isinstance(item, Track): coitems_track.append(item)
				else: raise Exception("Warning: Item type is not listed")
		coitems[Artist] = coitems_artist
		coitems[Genre] = coitems_genre
		coitems[Album] = coitems_album
		coitems[Track] = coitems_track
		return coitems
		
	@classmethod
	def get_similarity_score(cls, user1, user2):
		u1_rated_items = User.get_classified_rated_items(user1)
		u2_rated_items = User.get_classified_rated_items(user2)
		coitems = User.get_coitems(user1, user2)
		
		#cosine distance formula
		numerator = 0
		denominator_u1 = 0
		denominator_u2 = 0
		for item_type in u1_rated_items:
			if not len(coitems[item_type]) == 0:
				numerator = numerator + len(u1_rated_items[item_type]) * len(u2_rated_items[item_type])
			denominator_u1 = denominator_u1 + math.pow(len(u1_rated_items[item_type]), 2)
			denominator_u2 = denominator_u2 + math.pow(len(u2_rated_items[item_type]), 2)
		similarity = numerator / (math.pow(denominator_u1, 0.5) * math.pow(denominator_u2, 0.5))
		return similarity

	@classmethod
	def get_average_score_all_item_type(cls, user):
		total = 0
		for item, item_rating in user.rated_items.iteritems():
			total = total + item_rating
		return total / len(user.rated_items)
	
	@classmethod
	def get_average_score_item_type(cls, user, item_type):
		total = 0
		count = 0
		for item, item_rating in user.rated_items.iteritems():
			if isinstance(item, item_type): 
				total = total + item_rating
				count = count + 1
		if not count == 0:
			average = total / count
		else:
			average = None
		return average
		
class Item(object):
	def __init__(self, id = 0):
		self.id = id
	
	@classmethod	
	def get_similar_items(cls, item):
		if isinstance(item, Artist): return Artist.get_similar_items(item)
		if isinstance(item, Genre): return Genre.get_similar_items(item)
		if isinstance(item, Album): return Album.get_similar_items(item)
		if isinstance(item, Track): return Track.get_similar_items(item)

	@classmethod
	def read_line(cls, line):
		return cls(int(line))

	@classmethod
	def read_file(cls, filename):
		f = open(filename, "r")
		for line in f:
			item = cls.read_line(line.strip())
			cls.items[item.id] = item
		f.close()
		 
	@classmethod
	def find(cls, id):
		if cls == Item:
			if id in Artist.items: return Artist.items[id]
			if id in Genre.items: return Genre.items[id]
			if id in Album.items: return Album.items[id]
			if id in Track.items: return Track.items[id]
			raise Exception("Warning: Item type is not listed.")
		else:
			return cls.items[id]

class Artist(Item): 
	items = {}
	
	@classmethod
	def get_similar_items(cls, item):
		similar_items = []
		for i_id, i in Track.items.iteritems():
			if item == i.artist:
				similar_items.append(i)
		for i_id, i in Album.items.iteritems():
			if item == i.artist:
				similar_items.append(i)
		return similar_items

class Genre(Item):
	items = {}
	
	@classmethod
	def get_similar_items(cls, item):
		similar_items = []
		for i_id, i in Track.items.iteritems():
			if item in i.genre:
				similar_items.append(i)
		for i_id, i in Album.items.iteritems():
			if item in i.genre:
				similar_items.append(i)
		return similar_items

class Album(Item):
	items = {}
   
	def __init__(self, id = 0, artist = None, genre = None):
		Item.__init__(self, id)
		self.artist = artist
		self.genre = genre if genre else []	  
   
	@classmethod
	def read_line(cls, line):
		line = line.split("|")
		id = int(line[0])
		artist = Artist.find(int(line[1])) if line[1] != "None" else None
		genres = [Genre.find(int(gid)) for gid in line[2:]]
		return cls(id, artist, genres)
		
	@classmethod
	def get_similar_items(cls, item):
		similar_items = []
		for i_id, i in Track.items.iteritems():
			if item == i.artist:
				if not i.artist == None: similar_items.append(item.album)
		return similar_items
   
class Track(Item):
	items = {}
   
	def __init__(self, id = 0, album = None, artist = None, genre = None):
		Item.__init__(self, id)
		self.album = album
		self.artist = artist
		self.genre = genre if genre else []
	  
	@classmethod
	def read_line(cls, line):
		line = line.split("|")
		id = int(line[0])
		album = Album.find(int(line[1])) if line[1] != "None" else None
		artist = Artist.find(int(line[2])) if line[2] != "None" else None
		genres = [Genre.find(int(gid)) for gid in line[3:]]
		return cls(id, album, artist, genres)
		
	@classmethod
	def get_similar_items(cls, item):
		similar_items = []
		if not item.album == None: similar_items.append(item.album)
		if not item.artist == None: similar_items.append(item.artist)
		return similar_items

class main(object):
	def __init__(self): pass

	def print_matrix(self):
		print "Count of artists : " + str(len(Artist.items))
		print "Count of genres : " + str(len(Genre.items))
		print "Count of albums : " + str(len(Album.items))
		print "Count of tracks : " + str(len(Track.items))
		print "Count of users : " + str(len(User.users))
		
	def print_average_matrix(self):
		print "Average Matrix"
		print repr("UserID").rjust(13), repr("Count").rjust(10), repr("Average").rjust(10), repr("Avg Artist").rjust(10), repr("Avg Genre").rjust(10), repr("Avg Album").rjust(10), repr("Avg Track").rjust(10)
		for user_id, user in User.users.iteritems():
			average = User.get_average_score_all_item_type(user)
			print repr(user_id).rjust(10), repr(len(user.rated_items)).rjust(10), repr(average).rjust(10), repr(User.get_average_score_item_type(user, Artist)).rjust(10), repr(User.get_average_score_item_type(user, Genre)).rjust(10), repr(User.get_average_score_item_type(user, Album)).rjust(10), repr(User.get_average_score_item_type(user, Track)).rjust(10)
	
	def print_coitems_matrix(self):
		print "CoItem Matrix"
		print repr("UserID 1").rjust(13), repr("UserID 2").rjust(10), repr("CoArtist").rjust(10), repr("CoGenre").rjust(10), repr("CoAlbum").rjust(10), repr("CoTrack").rjust(10), repr("CoItem").rjust(10)
		for user_id1, user1 in User.users.iteritems():
			for user_id2, user2 in User.users.iteritems():
				coitems = User.get_coitems(user1, user2)
				coitems_total = len(coitems[Artist]) + len(coitems[Genre]) + len(coitems[Album]) + len(coitems[Track])
				print repr(user_id1).rjust(10), repr(user_id2).rjust(10), repr(len(coitems[Artist])).rjust(10), repr(len(coitems[Genre])).rjust(10), repr(len(coitems[Album])).rjust(10), repr(len(coitems[Track])).rjust(10), repr(coitems_total).rjust(10)
	
	def print_similarity_matrix(self):
		print "Similarity Matrix"
		print repr("UserID 1").rjust(13), repr("UserID 2").rjust(10), repr("Similarity Score").rjust(20)
		for user_id1, user1 in User.users.iteritems():
			for user_id2, user2 in User.users.iteritems():
				similarity_score = User.get_similarity_score(user1, user2)
				print repr(user_id1).rjust(10), repr(user_id2).rjust(10), repr(similarity_score).rjust(20)
	
	def print_prediction_matrix(self):
		if track_no == "1":
			print "Prediction Matrix"
			rmse_sum = 0
			count = 0
			for user_id, user in TestUser.users.iteritems():
				for item, item_rating in user.test_items.iteritems():
					predicted_score = TestUser.get_predicted_score(user, item)
					rmse = TestUser.get_rmse_score(item_rating, predicted_score)
					print user_id, item.id, item_rating, predicted_score, rmse
					count = count + 1
					rmse_sum = rmse_sum + rmse
			print "RMSE SCORE : ", math.sqrt(rmse_sum / count)
		else:
			print "Favourite / Not Favourite Matrix"
			error_count = 0.0
			all_count = 0.0
			
			#print 1 or 0 (favourable or unfavourable)
			for user_id, user in TestUser.users.iteritems():
				ps_favourite_count = 0
				ps_median = 0
				ps_score_list = []
				real_favourite_count = 0
				real_median = 0
				real_score_list = []
				
				#average score
				for item, item_rating in user.test_items.iteritems():
					predicted_score = TestUser.get_predicted_score(user, item)
					ps_score_list.append(predicted_score)
					real_score_list.append(item_rating)
				ps_score_list.sort()
				real_score_list.sort()
				ps_median = ps_score_list[2]
				real_median = real_score_list[2]
				
				#print 1 or 0 (favourable or unfavourable)
				for item, item_rating in user.test_items.iteritems():
					predicted_score = TestUser.get_predicted_score(user, item)
					ps_favourite = 0
					real_favourite = 0
					if ((predicted_score > ps_median) & (ps_favourite_count < 4)):
						ps_favourite = 1
						ps_favourite_count = ps_favourite_count + 1
					if ((item_rating > real_median) & (real_favourite_count < 4)):
						real_favourite = 1
						real_favourite_count = real_favourite_count + 1
					
					#counting error rate
					all_count = all_count + 1
					if not real_favourite == ps_favourite:
						error_count = error_count + 1
					print user_id, item.id, item_rating, real_favourite, predicted_score, ps_favourite

			#calculating error rate
			error_rate = error_count / all_count
			print "Error Rate : ", (error_count / all_count)
		
		def print_test_user_matrix(self):
			print "Count of test users : " + str(len(TestUser.users))
			for user_id, user in TestUser.users.iteritems():
				for item, item_rating in user.test_items.iteritems():
					print user_id, item.id, item_rating
	
	def generate_random_test_set(self):
		f = open('track2/testIdx2_random.txt', "w")
		f.write("OMG")
	
	def load_track1(self):
		global track_no 
		track_no = "1"
		Artist.read_file('track1/artistData1.txt')
		Genre.read_file('track1/genreData1.txt')
		Album.read_file('track1/albumData1.txt')
		Track.read_file('track1/trackData1.txt')
		User.read_file('track1/trainIdx.txt')
		TestUser.read_file('track1/testIdx1.txt')
	
	def load_track2(self):
		global track_no 
		track_no = "2"
		Artist.read_file('track2/artistData2.txt')
		Genre.read_file('track2/genreData2.txt')
		Album.read_file('track2/albumData2.txt')
		Track.read_file('track2/trackData2.txt')
		User.read_file('track2/trainIdx2.txt')
		TestUser.read_file('track2/testIdx2.txt')
		#TestUser.read_file('track2/trainIdx2_rm.txt')
		
	def main(self):
		self.load_track1()
		#self.load_track2()
		self.print_matrix()
		self.print_average_matrix()
		self.print_coitems_matrix()
		self.print_similarity_matrix()
		#self.print_test_user_matrix()
		self.print_prediction_matrix()
		
		#self.generate_random_test_set()
		

program = main()
program.main()

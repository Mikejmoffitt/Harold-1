import alsaaudio
import time
import os
import serial
import random
import json
import urllib2

timeHour = int(time.strftime('%H'))

playTime = 0

def init(baudrate):
	os.system("rm -f /tmp/mplayer.fifo")
	os.system("mkfifo /tmp/mplayer.fifo && mplayer -idle -slave -input file=/tmp/mplayer.fifo 1&>/dev/null &")
	ser = serial.Serial('/dev/ttyACM0', baudrate)
# If you enable this "ding" I will remove your gonads
# os.system("mplayer -slave -input file=/tmp/mplayer.fifo /home/pi/ding.mp3 &")
	ser.flushInput()
	return ser

playing = False
start = ""
varID = ""

ser = init(9600)

quietVolume = 60

ldapStr = "http://www.csh.rit.edu:56124/?ibutton="

# Pool of random songs for users without harold tracks in place
songs = [ "/users/u22/stuart/harold.mp3",
	"/users/u22/henry/harold.mp3",
	"/users/u22/mbillow/harold.mp3"
	"/users/u22/henry/harold/selfie.mp3",
	"/users/u22/henry/harold/waka.mp3",
	"/users/u22/henry/harold/topworld.mp3",
	"/users/u22/henry/harold/heybrother.mp3",
	"/users/u22/henry/harold/boomclap.mp3",
	"/users/u22/henry/harold/starships.mp3",
	"/users/u22/henry/harold/domino.mp3",
	"/users/u22/henry/harold/cruise.mp3"]

# Stuff your music into the mplayer FIFO
def playFile(fpath):
	os.system("echo \"loadFile '" + fpath + "'\" > /tmp/mplayer.fifo")

# Attenuate audio based on the time.
def setVolume(time):
	m = alsaaudio.Mixer(control='PCM')
	if (23 <= time <= 24) or (0 <= time <= 7):
		m.setvolume(quietvolume)
	else:
		m.setvolume(100)

def fadeOut():
	vol = int(m.getvolume()[0])
	# Uh, fade it out to 60 with some goofy math and then cut it off, I guess?
	while vol > 60:
		m.setvolume(vol)
		time.sleep(0.1)
		vol -= 1 + 1 / 3 * (100 - vol)

# If username retrieval failed, it will play a random song.
def tryHomeDirHarold(username, directory):
	if (username != "") and (os.access(directory + "\harold.mp3", os.R_OK)):
		playFile(directory + "\harold.mp3");
	else:
		playFile(songs[random.randint(0, len(songs)-1)]);

def haroldLoop():
	while 1:
		try:
			if not playing:
				varID = ser.readline()
				print(varID)
				if "ready" in varID:
					varID = ""
				# It shouldn't ding.
				# os.system("echo \"loadfile /home/pi/ding.mp3\" >/tmp/mplayer.fifo")
		except:
			pass

		setVolume(timeHour)
		if not playing and varID != "":
			try:
				# Get username from ibutton using this LDAP service
				usernameData = json.load(urllib2.urlopen(ldapStr + varID))
			except urllib2.HTTPError, error:
				# Check for returned error codes and do nothing with them
				contents = error.read()
				print(contents)
				username = ""

				# Not sure why this is set here; it would have been clearer if it wasn't
				# a re-used variable name called "dafile".
				homedir = songs[random.randint(0, len(songs)-1)]
			else:
				username = usernameData['username'][0]
				homedir = usernameData['homeDir'][0]

			print("New User: '" + username + "'")

			# Username retrieved, harold directory exists
			if (username != "") and (os.path.isdir(homedir + "/harold")):
				# Get a list of the files in the harold directory, choose one random file and play it
				playlistFiles = [f for f in os.listdir(homedir + "/harold") if os.path.isfile(homedir + "/harold/" + f) and f.endswith(".mp3") ]
				shuffleSong = playlistFiles[random.randint(0, len(playlistFiles)-1)]
				if len(playlistFiles) == 0:
					tryHomeDirHarold(username, homedir)
				else:
					playFile(homedir + "/harold/" + shuffleSong.replace("'", "\\'"))
			else:
				tryHomeDirHarold(username, homedir)
			# Wait for an arbitrary amount of time
			time.sleep(3)
			start = time.strftime("%s")
			playing = True

		elif playing and int(time.strftime("%s")) - int(start) >= 25:
			fadeOut()
			os.system("echo \"stop\" >/tmp/mplayer.fifo")
			playing = False
			ser.flushInput()
			print "Stopped\n"

def main():
	haroldLoop()

if __name == "__main__":
	main()

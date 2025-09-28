import xbmcgui
import xbmcaddon
import xbmc
import requests
import json
import threading
import sys
from library_service import AudioBookShelfLibraryService

class AudioBookPlayer(xbmcgui.WindowXMLDialog):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.id = kwargs['id']
		self.title = kwargs['title']
		self.cover = kwargs['cover']
		self.description = kwargs['description']
		self.narrator_name = kwargs['narrator_name']
		self.published_year = kwargs['published_year']
		self.publisher = kwargs['publisher']
		self.duration = kwargs['duration']
		self.player = xbmc.Player()
		self.library_service = AudioBookShelfLibraryService()
		self.chapters = self.library_service.get_chapters(self.id)
		self.threads = []
		
		# Progress tracking variables
		self.saved_progress = 0.0
		self.last_saved_time = 0.0
		self.progress_save_interval = 30  # Save progress every 30 seconds
		self.load_progress()

	def onInit(self):
		controls_mapping = {
			1: self.title,
			2: self.description,
			3: self.cover,
			4: self.narrator_name,
			5: self.published_year,
			6: self.publisher
		}
		for control_id, value in controls_mapping.items():
			control = self.getControl(control_id)
			if control_id in [1, 4, 5, 6]:  # Label controls
				control.setLabel(value)
			elif control_id == 2:  # Textbox control
				control.setText(value)
			elif control_id == 3:  # Image control
				control.setImage(value)

		self.button_controls = [
			self.getControl(1003), self.getControl(1002),
			self.getControl(1001), self.getControl(1010), self.getControl(1007),
			self.getControl(1008)
		]

		self.set_button_navigation()
		if self.button_controls:
			self.setFocus(self.button_controls[2])

	def set_button_navigation(self):
		for index, button in enumerate(self.button_controls):
			left_button = self.button_controls[index - 1] if index > 0 else button
			right_button = self.button_controls[index + 1] if index < len(self.button_controls) - 1 else button
			button.setNavigation(button, button, left_button, right_button)

	def update_progressbar(self):
		time = self.player.getTime()
		duration = self.duration
		progress_percentage = 0.0

		if not self.player.isPlaying():
			pass
		else:
			time = self.player.getTime()
			duration = self.duration
			progress_percentage = (time / duration) * 100 if duration != 0 else 0

		pb = self.getControl(1009)
		pb.setPercent(progress_percentage)

	def progressbar_updater(self):
		while self.player.isPlayingAudio():
			self.update_progressbar()
			self.auto_save_progress()
			xbmc.sleep(5000)

	def chapter_updater(self):
		while self.player.isPlayingAudio():
			self.update_chapter(self.player.getTime())
			xbmc.sleep(2000)				

	def get_chapter_by_time(self,time):
		for chapter in self.chapters:
			if chapter['start'] <= time <= chapter['end']:
				return chapter
		return None

	def update_chapter(self,time):
		current_chapter = self.get_chapter_by_time(time)
		ccontrol = self.getControl(1011)
		ccontrol.setLabel(current_chapter['title'])

	def get_next_chapter(self, time):
		current_chapter = None
		for chapter in self.chapters:
			if chapter['start'] <= time <= chapter['end']:
				current_chapter = chapter
				break
		if current_chapter and self.chapters.index(current_chapter) < len(self.chapters) - 1:
			return self.chapters[self.chapters.index(current_chapter) + 1]
		return None

	def get_previous_chapter(self, time):
		current_chapter = None
		for chapter in self.chapters:
			if chapter['start'] <= time <= chapter['end']:
				current_chapter = chapter
				break
		if current_chapter and self.chapters.index(current_chapter) > 0:
			return self.chapters[self.chapters.index(current_chapter) - 1]
		return None

	def update_timer(self):
		while self.player.isPlayingAudio():
			ct = self.player.getTime()
			
			# Umwandlung von Sekunden in Minuten und Sekunden
			minutes = int(ct // 60)
			seconds = int(ct % 60)

			# Formatierung der Ausgabe als MM:SS
			formatted_time = "{:02d}:{:02d}".format(minutes, seconds)

			timer_control = self.getControl(1012)
			timer_control.setLabel(formatted_time)        
			xbmc.sleep(500)

	def load_progress(self):
		"""Load saved progress from the server"""
		try:
			progress_data = self.library_service.get_media_progress(self.id)
			if progress_data and 'currentTime' in progress_data:
				self.saved_progress = float(progress_data['currentTime'])
				xbmc.log(f"Loaded progress for {self.id}: {self.saved_progress} seconds", xbmc.LOGINFO)
			else:
				self.saved_progress = 0.0
				xbmc.log(f"No saved progress found for {self.id}", xbmc.LOGINFO)
		except Exception as e:
			xbmc.log(f"Failed to load progress for {self.id}: {str(e)}", xbmc.LOGERROR)
			self.saved_progress = 0.0

	def save_progress(self, current_time=None):
		"""Save current progress to the server"""
		try:
			if current_time is None:
				if self.player.isPlayingAudio():
					current_time = self.player.getTime()
				else:
					current_time = self.last_saved_time

			if current_time > 0:
				progress_data = {
					'currentTime': current_time,
					'duration': self.duration,
					'progress': (current_time / self.duration) if self.duration > 0 else 0
				}
				
				self.library_service.update_media_progress(self.id, progress_data)
				self.last_saved_time = current_time
				xbmc.log(f"Saved progress for {self.id}: {current_time} seconds", xbmc.LOGDEBUG)
		except Exception as e:
			xbmc.log(f"Failed to save progress for {self.id}: {str(e)}", xbmc.LOGERROR)

	def auto_save_progress(self):
		"""Automatically save progress at regular intervals"""
		if self.player.isPlayingAudio():
			current_time = self.player.getTime()
			# Save progress if enough time has passed since last save
			if abs(current_time - self.last_saved_time) >= self.progress_save_interval:
				self.save_progress(current_time)

	def resume_from_progress(self):
		"""Resume playback from saved progress"""
		if self.saved_progress > 0:
			try:
				# Wait for player to be ready
				max_wait_time = 10
				wait_count = 0
				while not self.player.isPlayingAudio() and wait_count < max_wait_time:
					xbmc.sleep(1000)
					wait_count += 1
				
				if self.player.isPlayingAudio():
					xbmc.sleep(1000)  # Additional delay for stability
					self.player.seekTime(self.saved_progress)
					xbmc.log(f"Resumed playback at {self.saved_progress} seconds", xbmc.LOGINFO)
					# Update chapter display after seeking
					xbmc.sleep(1000)
					if self.player.isPlayingAudio():
						self.update_chapter(self.player.getTime())
			except Exception as e:
				xbmc.log(f"Failed to resume from progress: {str(e)}", xbmc.LOGERROR)	

	def _start_thread(self, target):
		thread = threading.Thread(target=target)
		thread.start()
		self.threads.append(thread)

	def onAction(self, action):
		if action.getId() == xbmcgui.ACTION_NAV_BACK:
			if self.player.isPlayingAudio():
				self.player.stop()
			self.close()
		elif action == xbmcgui.ACTION_SELECT_ITEM:
			focus_id = self.getFocusId()
			if focus_id == 1001:  # Play Button
				play_button = self.getControl(1001)
				afile = self.library_service.get_file_url(self.id)

				if self.player.isPlayingAudio():
					self.player.pause()
				else:
					self.player.play(afile)
					# Resume from saved progress after playback starts
					if self.saved_progress > 0:
						# Start thread to handle resume after playback initializes
						self._start_thread(self.resume_from_progress)

				while not self.getControl(1010).isVisible():
					xbmc.sleep(1000)
				self.setFocus(self.getControl(1010))

				self.update_chapter(self.player.getTime())
				self._start_thread(self.progressbar_updater)
				self._start_thread(self.chapter_updater)
				self._start_thread(self.update_timer)

			elif focus_id == 1010:  # Pause Button
				# Save progress before pausing
				if self.player.isPlayingAudio():
					try:
						current_time = self.player.getTime()
						self.save_progress(current_time)
					except:
						pass  # Continue if getting time fails
				
				self.player.pause()

				while not self.getControl(1001).isVisible():
					xbmc.sleep(1000)
				self.setFocus(self.getControl(1001))

			elif focus_id in [1003, 1008]:  # Chapter navigation buttons
				chapter = None
				if focus_id == 1003:
					chapter = self.get_previous_chapter(self.player.getTime())
				elif focus_id == 1008:
					chapter = self.get_next_chapter(self.player.getTime())
				
				if chapter:
					cs = chapter['start']
					self.player.seekTime(cs)
					# Save progress after seeking to new chapter
					self.save_progress(cs)

			elif focus_id in [1002, 1007]:  # Time navigation buttons
				ct = self.player.getTime()
				st = None
				if focus_id == 1002:
					st = ct - 10
				elif focus_id == 1007:
					st = ct + 10

				if st is not None:
					# Ensure we don't seek to negative time
					st = max(0, st)
					self.player.seekTime(st)
					# Save progress after seeking
					self.save_progress(st)

	def close(self):
		# Save progress before closing
		if self.player.isPlayingAudio():
			try:
				current_time = self.player.getTime()
				self.save_progress(current_time)
			except:
				pass  # Continue closing if saving fails
			self.player.stop()

		for thread in self.threads:
			if thread.is_alive():
				thread.join(timeout=2)

		super().close()		
				
					
if __name__ == "__main__":
	if "play" in sys.argv:
		xbmcgui.Dialog().notification('Audiobook Player', 'Play Funktion hier!', xbmcgui.NOTIFICATION_INFO, 2000)
	else:
		myDialog = AudioBookPlayer('audiobook_dialog.xml', xbmcaddon.Addon().getAddonInfo('path'))
		myDialog.doModal()
		del myDialog

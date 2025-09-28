# Audiobook Progress Tracking Feature

## Overview

This update adds comprehensive progress tracking and resume functionality to the AudiobookShelf simple client. Users can now:

- **Automatically save progress** while listening to audiobooks
- **Resume from where they left off** when restarting playback
- **See progress indicators** in the library view for books that have been started
- **Progress synchronization** with the AudiobookShelf server

## Features Added

### 1. Automatic Progress Saving

- Progress is automatically saved every 30 seconds during playback
- Progress is saved when pausing, seeking (chapter/time navigation), or closing the player
- All progress data is synchronized with the AudiobookShelf server

### 2. Resume Functionality

- When starting playback, the client checks for existing progress on the server
- If progress is found, playback automatically resumes from the saved position
- The resume process waits for the player to initialize properly before seeking
- Chapter information is updated after resuming

### 3. Visual Progress Indicators

- The main library view now shows progress percentages for books that have been started
- Books with more than 1% progress completed show "Book Title (XX%)" format
- Original titles are preserved for the player interface

### 4. Robust Error Handling

- Progress loading/saving continues to work even if individual operations fail
- Network issues or server problems won't prevent playback
- Graceful fallbacks ensure the player remains functional

## Technical Implementation

### Modified Files

#### `audio_book.py`
- Added progress tracking variables (`saved_progress`, `last_saved_time`, `progress_save_interval`)
- New methods:
  - `load_progress()` - Loads saved progress from server on initialization
  - `save_progress(current_time)` - Saves progress to server
  - `auto_save_progress()` - Automatic interval-based saving during playback
  - `resume_from_progress()` - Resumes playback from saved position
- Enhanced existing methods to integrate progress saving:
  - Play button now resumes from saved progress
  - Pause button saves progress before pausing
  - Chapter/time navigation saves progress after seeking
  - Close method saves final progress before exit

#### `default.py`
- Modified `select_library()` function to fetch progress information for each audiobook
- Added progress indicators to audiobook titles in the library view
- Preserved original titles for the player while showing progress in the UI
- Enhanced `show_audiobook_player()` to use original titles

#### `library_service.py` (unchanged, already had required API methods)
- `get_media_progress(library_item_id)` - Gets current progress from server
- `update_media_progress(library_item_id, data)` - Updates progress on server

## API Integration

The progress tracking leverages the existing AudiobookShelf API endpoints:

- `GET /api/me/progress/{itemId}` - Retrieve user's progress for an item
- `PATCH /api/me/progress/{itemId}` - Update user's progress for an item

Progress data format:
```json
{
  "currentTime": 1234.5,    // Current playback position in seconds
  "duration": 3600.0,       // Total duration in seconds
  "progress": 0.343         // Progress as decimal (0.0 to 1.0)
}
```

## User Experience

### Starting a New Book
1. User selects a book from the library
2. Playback starts from the beginning (position 0:00)
3. Progress is automatically saved every 30 seconds

### Resuming a Book
1. User selects a book they've previously started (shows progress percentage)
2. Playback starts and automatically seeks to the saved position
3. A brief pause occurs while the player initializes and seeks
4. Playbook continues from where it was left off
5. Chapter information updates to reflect the current position

### Progress Indicators
- **New books**: Show normal title (e.g., "The Great Gatsby")
- **Started books**: Show title with progress (e.g., "The Great Gatsby (34%)")
- Progress is calculated and displayed as a percentage of completion

### Manual Actions That Save Progress
- Pressing pause
- Seeking to different chapters (previous/next chapter buttons)
- Seeking in time (10-second forward/backward buttons)
- Closing the player or going back to the library

## Configuration

The progress save interval can be adjusted by modifying the `progress_save_interval` variable in the `AudioBookPlayer.__init__()` method:

```python
self.progress_save_interval = 30  # Save progress every 30 seconds
```

## Error Handling

The implementation includes comprehensive error handling:

- **Network failures**: Progress saving fails gracefully without affecting playbook
- **Server unavailable**: Client continues to function with local player state
- **Invalid progress data**: Defaults to starting from the beginning
- **Player initialization issues**: Resume functionality includes timeout protection

## Performance Considerations

- Progress is only saved when there are actual changes (not redundant saves)
- Network calls are made asynchronously to avoid blocking the UI
- Minimal impact on playbook performance with 30-second save intervals
- Server requests are only made for actual progress updates

## Future Enhancements

Potential improvements for future versions:

1. **Offline progress caching** - Store progress locally when server is unavailable
2. **Multiple position bookmarks** - Allow users to set custom bookmarks
3. **Progress synchronization across devices** - Real-time progress updates
4. **Reading statistics** - Track listening time, completion rates, etc.
5. **Progress export/import** - Backup and restore progress data

## Testing

To test the progress tracking functionality:

1. Start playing an audiobook and let it play for a few minutes
2. Close the player and restart the book - it should resume from where you left off
3. Navigate using chapter or time controls - progress should be saved
4. Check the library view - started books should show progress percentages
5. Try pausing and resuming - progress should be maintained

## Troubleshooting

### Progress Not Saving
- Check network connectivity to AudiobookShelf server
- Verify user authentication token is valid
- Check Kodi logs for error messages related to progress saving

### Resume Not Working
- Ensure the book was played long enough for progress to be saved (>30 seconds)
- Check that the AudiobookShelf server has the progress data
- Verify the player initializes properly before resume attempts

### Progress Percentages Not Showing
- Confirm the library service can fetch progress data from the server
- Check that audiobook durations are correctly stored in the server
- Verify progress calculation logic is working correctly

The progress tracking feature significantly enhances the user experience by providing seamless audiobook consumption across sessions while maintaining full compatibility with the existing AudiobookShelf ecosystem.
import asyncio
import os
import tempfile
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from pyrogram.errors import FloodWait
from helper.helper_func import encode
from helper.screenshot_helper import extract_screenshots, cleanup_temp_files, check_ffmpeg_installed

#===============================================================#

async def process_video_with_screenshots(client: Client, message: Message, reply_text: Message):
    """
    Process a video message: extract screenshots and upload as batch with video.
    Returns tuple of (batch_link, screenshot_paths) or (None, []) if failed.
    """
    video_path = None
    screenshot_paths = []
    
    try:
        # Check if FFmpeg is available
        ffmpeg_available = await check_ffmpeg_installed()
        if not ffmpeg_available:
            client.LOGGER(__name__, client.name).warning("FFmpeg not installed, skipping screenshot extraction")
            return None, []
        
        await reply_text.edit_text("📥 Downloading video...")
        
        # Download the video to a temporary file
        temp_dir = tempfile.mkdtemp(prefix="video_")
        video_path = await message.download(file_name=os.path.join(temp_dir, "video"))
        
        if not video_path or not os.path.exists(video_path):
            client.LOGGER(__name__, client.name).error("Failed to download video")
            return None, []
        
        await reply_text.edit_text("📸 Extracting screenshots...")
        
        # Extract screenshots from the video
        screenshot_paths = await extract_screenshots(video_path, num_screenshots=4)
        
        if not screenshot_paths:
            client.LOGGER(__name__, client.name).warning("No screenshots extracted, falling back to normal upload")
            return None, []
        
        await reply_text.edit_text("📤 Uploading to database...")
        
        # Upload screenshots as a media group first
        media_group = []
        for i, ss_path in enumerate(screenshot_paths):
            caption = f"📸 Screenshot {i+1}" if i == 0 else None
            media_group.append(InputMediaPhoto(media=ss_path, caption=caption))
        
        # Send screenshots to DB channel
        try:
            screenshot_messages = await client.send_media_group(
                chat_id=client.db,
                media=media_group,
                disable_notification=True
            )
            first_msg_id = screenshot_messages[0].id
        except FloodWait as e:
            await asyncio.sleep(e.x)
            screenshot_messages = await client.send_media_group(
                chat_id=client.db,
                media=media_group,
                disable_notification=True
            )
            first_msg_id = screenshot_messages[0].id
        
        # Upload the original video to DB channel
        try:
            video_message = await message.copy(chat_id=client.db, disable_notification=True)
            last_msg_id = video_message.id
        except FloodWait as e:
            await asyncio.sleep(e.x)
            video_message = await message.copy(chat_id=client.db, disable_notification=True)
            last_msg_id = video_message.id
        
        # Generate batch link (screenshots + video)
        string = f"get-{first_msg_id * abs(client.db)}-{last_msg_id * abs(client.db)}"
        base64_string = await encode(string)
        link = f"https://t.me/{client.username}?start={base64_string}"
        
        return link, screenshot_paths
        
    except Exception as e:
        client.LOGGER(__name__, client.name).error(f"Error processing video with screenshots: {e}")
        return None, []
    finally:
        # Cleanup video file only (keep screenshots for sending to user)
        if video_path and os.path.exists(video_path):
            cleanup_temp_files([video_path])


@Client.on_message(filters.private & ~filters.command(['start', 'shortner','users','broadcast','batch','genlink','stats', 'pbroadcast', 'db', 'adddb', 'add_db', 'removedb', 'rm_db',  'ban', 'unban', 'addpremium', 'delpremium', 'premiumusers', 'request', 'profile']))
async def channel_post(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(client.reply_text)
    
    reply_text = await message.reply_text("Please Wait...!", quote=True)
    
    # Check if message contains a video
    is_video = bool(message.video or (message.document and message.document.mime_type and message.document.mime_type.startswith('video/')))
    
    if is_video:
        # Process video with screenshot extraction
        link, screenshot_paths = await process_video_with_screenshots(client, message, reply_text)
        
        if link and screenshot_paths:
            # Delete the "Please wait" message
            await reply_text.delete()
            
            # Send screenshots to the user with the link
            try:
                media_group = []
                caption_text = (
                    f"<b>Here is your link</b>\n\n"
                    f"{link}"
                )
                
                for i, ss_path in enumerate(screenshot_paths):
                    # Add caption only to first screenshot
                    caption = caption_text if i == 0 else None
                    media_group.append(InputMediaPhoto(media=ss_path, caption=caption))
                
                # Send screenshots to user
                await client.send_media_group(
                    chat_id=message.from_user.id,
                    media=media_group
                )
                
                # Send the share button as a separate message
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]
                ])
                await message.reply_text(
                    f"<a href='{link}'>🔗 Batch Link</a>",
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
                
                # Cleanup screenshots after sending
                cleanup_temp_files(screenshot_paths)
                
            except Exception as e:
                client.LOGGER(__name__, client.name).error(f"Error sending screenshots to user: {e}")
                # Fallback to text only
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]
                ])
                await reply_text.edit(
                    f"<b>✅ Video processed with screenshots!</b>\n\n"
                    f"<b>📎 Batch Link:</b>\n<code>{link}</code>",
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
                cleanup_temp_files(screenshot_paths)
            
            return
        # If screenshot extraction failed, fall through to normal processing
    
    # Normal file processing (non-video or failed screenshot extraction)
    try:
        post_message = await message.copy(chat_id=client.db, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id=client.db, disable_notification=True)
    except Exception as e:
        print(e)
        await reply_text.edit_text("Something went Wrong..!")
        return
    
    converted_id = post_message.id * abs(client.db)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])

    await reply_text.edit(f"<b>Here is your link</b>\n\n{link}", reply_markup=reply_markup, disable_web_page_preview=True)

    if not client.disable_btn:
        await post_message.edit_reply_markup(reply_markup)

#===============================================================#

@Client.on_message(filters.channel & filters.incoming)
async def new_post(client: Client, message: Message):
    if message.chat.id != client.db:
        return
    if client.disable_btn:
        return

    converted_id = message.id * abs(client.db)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    try:
        await message.edit_reply_markup(reply_markup)
    except Exception as e:
        print(e)

        pass






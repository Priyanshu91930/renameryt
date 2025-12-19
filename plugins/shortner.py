import requests
import random
import string
from config import SHORT_URL, SHORT_API, MESSAGES
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram.errors.pyromod import ListenerTimeout
from helper.helper_func import force_sub

# ✅ In-memory cache
shortened_urls_cache = {}

def generate_random_alphanumeric():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(8))

def get_short(url, client, force_shorten=False):
    """
    Shorten a URL using the configured shortener service.
    
    Args:
        url: The URL to shorten
        client: The bot client
        force_shorten: If True, ignore shortner_enabled setting and always try to shorten
    """
    # Check if shortner is enabled (unless force_shorten is True)
    if not force_shorten:
        shortner_enabled = getattr(client, 'shortner_enabled', True)
        if not shortner_enabled:
            return url  # Return original URL if shortner is disabled

    # Step 2: Check cache
    if url in shortened_urls_cache:
        return shortened_urls_cache[url]

    try:
        alias = generate_random_alphanumeric()
        # Use dynamic shortner settings from client if available
        short_url = getattr(client, 'short_url', SHORT_URL)
        short_api = getattr(client, 'short_api', SHORT_API)
        
        api_url = f"https://{short_url}/api?api={short_api}&url={url}&alias={alias}"
        response = requests.get(api_url)
        rjson = response.json()

        if rjson.get("status") == "success" and response.status_code == 200:
            short_url = rjson.get("shortenedUrl", url)
            shortened_urls_cache[url] = short_url
            return short_url
    except Exception as e:
        print(f"[Shortener Error] {e}")

    return url  # fallback

#===============================================================#

@Client.on_message(filters.command('shortner') & filters.private)
async def shortner_command(client: Client, message: Message):
    await shortner_panel(client, message)

#===============================================================#

async def shortner_panel(client, query_or_message):
    # Get current shortner settings
    short_url = getattr(client, 'short_url', SHORT_URL)
    short_api = getattr(client, 'short_api', SHORT_API)
    tutorial_link = getattr(client, 'tutorial_link', "https://t.me/How_to_Download_7x/26")
    shortner_enabled = getattr(client, 'shortner_enabled', True)
    
    # Check if shortner is working (only if enabled)
    if shortner_enabled:
        try:
            test_response = requests.get(f"https://{short_url}/api?api={short_api}&url=https://google.com&alias=test", timeout=5)
            status = "✓ ᴡᴏʀᴋɪɴɢ" if test_response.status_code == 200 else "✗ ɴᴏᴛ ᴡᴏʀᴋɪɴɢ"
        except:
            status = "✗ ɴᴏᴛ ᴡᴏʀᴋɪɴɢ"
    else:
        status = "✗ ᴅɪsᴀʙʟᴇᴅ"
    
    enabled_text = "✓ ᴇɴᴀʙʟᴇᴅ" if shortner_enabled else "✗ ᴅɪsᴀʙʟᴇᴅ"
    toggle_text = "✗ ᴏғғ" if shortner_enabled else "✓ ᴏɴ"
    
    msg = f"""<blockquote>✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦</blockquote>
**<u>ᴄᴜʀʀᴇɴᴛ ꜱᴇᴛᴛɪɴɢꜱ:</u>**
<blockquote>›› **ꜱʜᴏʀᴛɴᴇʀ ꜱᴛᴀᴛᴜꜱ:** {enabled_text}
›› **ꜱʜᴏʀᴛɴᴇʀ ᴜʀʟ:** `{short_url}`
›› **ꜱʜᴏʀᴛɴᴇʀ ᴀᴘɪ:** `{short_api}`</blockquote> 
<blockquote>›› **ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ:** `{tutorial_link}`
›› **ᴀᴘɪ ꜱᴛᴀᴛᴜꜱ:** {status}</blockquote>

<blockquote>**≡ ᴜꜱᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ ᴛᴏ ᴄᴏɴꜰɪɢᴜʀᴇ ʏᴏᴜʀ ꜱʜᴏʀᴛɴᴇʀ ꜱᴇᴛᴛɪɴɢꜱ!**</blockquote>"""
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f'• {toggle_text} ꜱʜᴏʀᴛɴᴇʀ •', 'toggle_shortner'), InlineKeyboardButton('• ᴀᴅᴅ ꜱʜᴏʀᴛɴᴇʀ •', 'add_shortner')],
        [InlineKeyboardButton('• ꜱᴇᴛ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ •', 'set_tutorial_link')],
        [InlineKeyboardButton('• ᴛᴇꜱᴛ ꜱʜᴏʀᴛɴᴇʀ •', 'test_shortner')],
        [InlineKeyboardButton('◂ ʙᴀᴄᴋ ᴛᴏ ꜱᴇᴛᴛɪɴɢꜱ', 'settings_page_2')] if hasattr(query_or_message, 'message') else []
    ])
    
    image_url = MESSAGES.get("SHORT", "https://telegra.ph/file/8aaf4df8c138c6685dcee-05d3b183d4978ec347.jpg")
    
    if hasattr(query_or_message, 'message'):
        await query_or_message.message.edit_media(
            media=InputMediaPhoto(media=image_url, caption=msg),
            reply_markup=reply_markup
        )
    else:
        await query_or_message.reply_photo(photo=image_url, caption=msg, reply_markup=reply_markup)


#===============================================================#

@Client.on_callback_query(filters.regex("^shortner$"))
async def shortner_callback(client, query):
    if not query.from_user.id in client.admins:
        return await query.answer('❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ!', show_alert=True)
    await query.answer()
    await shortner_panel(client, query)

#===============================================================#

@Client.on_callback_query(filters.regex("^toggle_shortner$"))
async def toggle_shortner(client: Client, query: CallbackQuery):
    if not query.from_user.id in client.admins:
        return await query.answer('❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ!', show_alert=True)
    # Toggle the shortner status
    current_status = getattr(client, 'shortner_enabled', True)
    new_status = not current_status
    client.shortner_enabled = new_status
    
    # Save to database
    await client.mongodb.set_shortner_status(new_status)
    
    status_text = "ᴇɴᴀʙʟᴇᴅ" if new_status else "ᴅɪsᴀʙʟᴇᴅ"
    await query.answer(f"✓ ꜱʜᴏʀᴛɴᴇʀ {status_text}!")
    
    # Refresh the panel
    await shortner_panel(client, query)

#===============================================================#

@Client.on_callback_query(filters.regex("^add_shortner$"))
async def add_shortner(client: Client, query: CallbackQuery):
    if not query.from_user.id in client.admins:
        return await query.answer('❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ!', show_alert=True)
    
    await query.answer()
        
    current_url = getattr(client, 'short_url', SHORT_URL)
    current_api = getattr(client, 'short_api', SHORT_API)
    
    msg = f"""<blockquote>**ꜱᴇᴛ ꜱʜᴏʀᴛɴᴇʀ ꜱᴇᴛᴛɪɴɢꜱ:**</blockquote>
**ᴄᴜʀʀᴇɴᴛ ꜱᴇᴛᴛɪɴɢꜱ:**
• **ᴜʀʟ:** `{current_url}`
• **ᴀᴘɪ:** `{current_api[:20]}...`

__<blockquote>**≡ ꜱᴇɴᴅ ɴᴇᴡ ꜱʜᴏʀᴛɴᴇʀ ᴜʀʟ ᴀɴᴅ ᴀᴘɪ ɪɴ ᴛʜɪꜱ ꜰᴏʀᴍᴀᴛ ɪɴ ᴛʜᴇ ɴᴇxᴛ 60 ꜱᴇᴄᴏɴᴅꜱ!**</blockquote>__

**ꜰᴏʀᴍᴀᴛ:** `ᴜʀʟ ᴀᴘɪ`
**ᴇxᴀᴍᴘʟᴇ:** `inshorturl.com 9435894656863495834957348`"""
    
    await query.message.edit_text(msg)
    try:
        res = await client.listen(user_id=query.from_user.id, filters=filters.text, timeout=60)
        response_text = res.text.strip()
        
        # Parse the response: url api
        parts = response_text.split()
        if len(parts) >= 2:
            new_url = parts[0].replace('https://', '').replace('http://', '').replace('/', '')
            new_api = ' '.join(parts[1:])  # Join remaining parts as API key
            
            if new_url and '.' in new_url and new_api and len(new_api) > 10:
                # Update both settings
                client.short_url = new_url
                client.short_api = new_api
                
                # Save to database
                await client.mongodb.update_shortner_setting('short_url', new_url)
                await client.mongodb.update_shortner_setting('short_api', new_api)
                
                await query.message.edit_text(f"**✓ ꜱʜᴏʀᴛɴᴇʀ ꜱᴇᴛᴛɪɴɢꜱ ᴜᴘᴅᴀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**\n\n**ɴᴇᴡ ᴜʀʟ:** `{new_url}`\n**ɴᴇᴡ ᴀᴘɪ:** `{new_api[:20]}...`", 
                                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'shortner')]]))
            else:
                await query.message.edit_text("**✗ ɪɴᴠᴀʟɪᴅ ꜰᴏʀᴍᴀᴛ! ᴘʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ᴜʀʟ ᴀɴᴅ ᴀᴘɪ ᴋᴇʏ.**", 
                                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'shortner')]]))
        else:
            await query.message.edit_text("**✗ ɪɴᴠᴀʟɪᴅ ꜰᴏʀᴍᴀᴛ! ᴘʟᴇᴀꜱᴇ ᴜꜱᴇ: `ᴜʀʟ ᴀᴘɪ`**", 
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'shortner')]]))
    except ListenerTimeout:
        await query.message.edit_text("**⏰ ᴛɪᴍᴇᴏᴜᴛ! ᴛʀʏ ᴀɢᴀɪɴ.**", 
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'shortner')]]))

#===============================================================#

@Client.on_callback_query(filters.regex("^set_tutorial_link$"))
async def set_tutorial_link(client: Client, query: CallbackQuery):
    if not query.from_user.id in client.admins:
        return await query.answer('❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ!', show_alert=True)
    
    await query.answer()
        
    current_tutorial = getattr(client, 'tutorial_link', "https://t.me/How_to_Download_7x/26")
    msg = f"""<blockquote>**ꜱᴇᴛ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ:**</blockquote>
**ᴄᴜʀʀᴇɴᴛ ᴛᴜᴛᴏʀɪᴀʟ:** `{current_tutorial}`

__ꜱᴇɴᴅ ᴛʜᴇ ɴᴇᴡ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ ɪɴ ᴛʜᴇ ɴᴇxᴛ 60 ꜱᴇᴄᴏɴᴅꜱ!__
**ᴇxᴀᴍᴘʟᴇ:** `https://t.me/How_to_Download_7x/26`"""
    
    await query.message.edit_text(msg)
    try:
        res = await client.listen(user_id=query.from_user.id, filters=filters.text, timeout=60)
        new_tutorial = res.text.strip()
        
        if new_tutorial and (new_tutorial.startswith('https://') or new_tutorial.startswith('http://')):
            client.tutorial_link = new_tutorial
            # Save to database
            await client.mongodb.update_shortner_setting('tutorial_link', new_tutorial)
            await query.message.edit_text(f"**✓ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ ᴜᴘᴅᴀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**", 
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'shortner')]]))
        else:
            await query.message.edit_text("**✗ ɪɴᴠᴀʟɪᴅ ʟɪɴᴋ ꜰᴏʀᴍᴀᴛ! ᴍᴜꜱᴛ ꜱᴛᴀʀᴛ ᴡɪᴛʜ https:// ᴏʀ http://**", 
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'shortner')]]))
    except ListenerTimeout:
        await query.message.edit_text("**⏰ ᴛɪᴍᴇᴏᴜᴛ! ᴛʀʏ ᴀɢᴀɪɴ.**", 
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'shortner')]]))

#===============================================================#

@Client.on_callback_query(filters.regex("^test_shortner$"))
async def test_shortner(client: Client, query: CallbackQuery):
    if not query.from_user.id in client.admins:
        return await query.answer('❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ!', show_alert=True)
    
    await query.answer()
        
    await query.message.edit_text("**🔄 ᴛᴇꜱᴛɪɴɢ ꜱʜᴏʀᴛɴᴇʀ...**")
    
    short_url = getattr(client, 'short_url', SHORT_URL)
    short_api = getattr(client, 'short_api', SHORT_API)
    
    try:
        test_url = "https://google.com"
        alias = generate_random_alphanumeric()
        api_url = f"https://{short_url}/api?api={short_api}&url={test_url}&alias={alias}"
        
        response = requests.get(api_url, timeout=10)
        rjson = response.json()
        
        if rjson.get("status") == "success" and response.status_code == 200:
            short_link = rjson.get("shortenedUrl", "")
            msg = f"""**✅ ꜱʜᴏʀᴛɴᴇʀ ᴛᴇꜱᴛ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ!**

**ᴛᴇꜱᴛ ᴜʀʟ:** `{test_url}`
**ꜱʜᴏʀᴛ ᴜʀʟ:** `{short_link}`
**ʀᴇꜱᴘᴏɴꜱᴇ:** `{rjson.get('status', 'Unknown')}`"""
        else:
            msg = f"""**❌ ꜱʜᴏʀᴛɴᴇʀ ᴛᴇꜱᴛ ꜰᴀɪʟᴇᴅ!**

**ᴇʀʀᴏʀ:** `{rjson.get('message', 'Unknown error')}`
**ꜱᴛᴀᴛᴜꜱ ᴄᴏᴅᴇ:** `{response.status_code}`"""
            
    except Exception as e:
        msg = f"**❌ ꜱʜᴏʀᴛɴᴇʀ ᴛᴇꜱᴛ ꜰᴀɪʟᴇᴅ!**\n\n**ᴇʀʀᴏʀ:** `{str(e)}`"
    
    await query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'shortner')]]))

#===============================================================#

@Client.on_callback_query(filters.regex("^access_token$"))
async def access_token_panel(client: Client, query: CallbackQuery):
    """Display Access Token settings panel"""
    if not query.from_user.id in client.admins:
        return await query.answer('❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ!', show_alert=True)
    
    await query.answer()
    
    # Get access token settings
    token_settings = await client.mongodb.get_access_token_settings()
    enabled = token_settings.get('enabled', False)
    validity_hours = token_settings.get('validity_hours', 12)
    renewed_count = await client.mongodb.get_renewed_users_count()
    
    enabled_emoji = "✅" if enabled else "❌"
    status_text = "Enabled" if enabled else "Disabled"
    
    msg = f"""<blockquote><b>Access Token</b></blockquote>

<i>Users need to pass a shortened link to gain special access to messages from all clone shareable links. This access will be valid for the next custom validity period.</i>

~ <b>Status:</b> {status_text} {enabled_emoji}
~ <b>Validity:</b> {validity_hours} hours
~ <b>Renewed:</b> {renewed_count} users"""
    
    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Toggle Status', 'toggle_access_token'),
            InlineKeyboardButton('Validity', 'set_token_validity')
        ],
        [
            InlineKeyboardButton('Users', 'token_users'),
            InlineKeyboardButton('Stats', 'token_stats')
        ],
        [
            InlineKeyboardButton('Revoke All', 'revoke_all_tokens'),
            InlineKeyboardButton('◂ Back', 'settings_page_2')
        ]
    ])
    
    await query.message.edit_text(msg, reply_markup=reply_markup)

#===============================================================#

@Client.on_callback_query(filters.regex("^toggle_access_token$"))
async def toggle_access_token(client: Client, query: CallbackQuery):
    """Toggle Access Token feature on/off"""
    if not query.from_user.id in client.admins:
        return await query.answer('❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ!', show_alert=True)
    
    # Get current status and toggle
    token_settings = await client.mongodb.get_access_token_settings()
    current_status = token_settings.get('enabled', False)
    new_status = not current_status
    
    # Update in database
    await client.mongodb.update_access_token_setting('enabled', new_status)
    
    # Update client attribute
    client.access_token_enabled = new_status
    
    status_text = "ᴇɴᴀʙʟᴇᴅ" if new_status else "ᴅɪsᴀʙʟᴇᴅ"
    await query.answer(f"✓ ᴀᴄᴄᴇss ᴛᴏᴋᴇɴ {status_text}!")
    
    # Refresh the panel
    await access_token_panel(client, query)

#===============================================================#

@Client.on_callback_query(filters.regex("^set_token_validity$"))
async def set_token_validity(client: Client, query: CallbackQuery):
    """Set Access Token validity period in hours"""
    if not query.from_user.id in client.admins:
        return await query.answer('❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ!', show_alert=True)
    
    await query.answer()
    
    token_settings = await client.mongodb.get_access_token_settings()
    current_validity = token_settings.get('validity_hours', 12)
    
    msg = f"""<blockquote><b>Set Token Validity Period:</b></blockquote>
<b>Current Validity:</b> <code>{current_validity} hours</code>

<i>Send the new validity period in hours (1-720) in the next 60 seconds!</i>

<b>Examples:</b>
• <code>12</code> - 12 hours
• <code>24</code> - 1 day
• <code>168</code> - 1 week
• <code>720</code> - 30 days"""
    
    await query.message.edit_text(msg)
    try:
        res = await client.listen(user_id=query.from_user.id, filters=filters.text, timeout=60)
        hours_text = res.text.strip()
        
        if hours_text.isdigit():
            hours = int(hours_text)
            if 1 <= hours <= 720:
                # Update in database
                await client.mongodb.update_access_token_setting('validity_hours', hours)
                
                # Update client attribute
                client.access_token_validity = hours
                
                await query.message.edit_text(f"**✓ ᴛᴏᴋᴇɴ ᴠᴀʟɪᴅɪᴛʏ ᴜᴘᴅᴀᴛᴇᴅ ᴛᴏ {hours} ʜᴏᴜʀs!**", 
                                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'access_token')]]))
            else:
                await query.message.edit_text("**✗ ɪɴᴠᴀʟɪᴅ ᴠᴀʟᴜᴇ! ᴍᴜsᴛ ʙᴇ ʙᴇᴛᴡᴇᴇɴ 1 ᴀɴᴅ 720 ʜᴏᴜʀs.**", 
                                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'access_token')]]))
        else:
            await query.message.edit_text("**✗ ɪɴᴠᴀʟɪᴅ ɪɴᴘᴜᴛ! ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ɴᴜᴍʙᴇʀ.**", 
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'access_token')]]))
    except ListenerTimeout:
        await query.message.edit_text("**⏰ ᴛɪᴍᴇᴏᴜᴛ! ᴛʀʏ ᴀɢᴀɪɴ.**", 
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'access_token')]]))

#===============================================================#

@Client.on_callback_query(filters.regex("^token_stats$"))
async def token_stats(client: Client, query: CallbackQuery):
    """Display Access Token statistics"""
    if not query.from_user.id in client.admins:
        return await query.answer('❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ!', show_alert=True)
    
    await query.answer()
    
    # Get stats
    token_settings = await client.mongodb.get_access_token_settings()
    enabled = token_settings.get('enabled', False)
    validity_hours = token_settings.get('validity_hours', 12)
    renewed_count = await client.mongodb.get_renewed_users_count()
    
    msg = f"""<blockquote><b>📊 Access Token Statistics</b></blockquote>

<b>Current Settings:</b>
• <b>Status:</b> {"✅ Enabled" if enabled else "❌ Disabled"}
• <b>Validity Period:</b> {validity_hours} hours

<b>Usage Stats:</b>
• <b>Active Tokens:</b> {renewed_count} users
• <b>Tokens grant access for:</b> {validity_hours} hours

<i>Active tokens = users who can access files without shortlink</i>"""
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('◂ ʙᴀᴄᴋ', 'access_token')]
    ])
    
    await query.message.edit_text(msg, reply_markup=reply_markup)

#===============================================================#

@Client.on_callback_query(filters.regex("^token_users$"))
async def token_users(client: Client, query: CallbackQuery):
    """Display list of users with active access tokens"""
    if not query.from_user.id in client.admins:
        return await query.answer('❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ!', show_alert=True)
    
    await query.answer()
    
    # Get all users with access
    users = await client.mongodb.get_access_users()
    
    if not users:
        msg = """<blockquote><b>👥 Access Token Users</b></blockquote>

<i>No users currently have active access tokens.</i>

<b>Users will appear here when they pass through the verification link.</b>"""
    else:
        user_list = ""
        for i, user in enumerate(users[:20], 1):  # Show max 20 users
            expiry = user['expiry'].strftime("%d/%m %H:%M") if user['expiry'] else "Unknown"
            user_list += f"<code>{i}. {user['user_id']}</code> - expires: {expiry}\n"
        
        if len(users) > 20:
            user_list += f"\n<i>...and {len(users) - 20} more</i>"
        
        msg = f"""<blockquote><b>👥 Access Token Users</b></blockquote>

<b>Active Tokens:</b> {len(users)} users

{user_list}
<i>To revoke a user's access, use:</i>
<code>/revoke_access USER_ID</code>"""
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('🔄 Refresh', 'token_users')],
        [InlineKeyboardButton('◂ Back', 'access_token')]
    ])
    
    await query.message.edit_text(msg, reply_markup=reply_markup)

#===============================================================#

@Client.on_callback_query(filters.regex("^revoke_all_tokens$"))
async def revoke_all_tokens(client: Client, query: CallbackQuery):
    """Revoke all access tokens"""
    if not query.from_user.id in client.admins:
        return await query.answer('❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ!', show_alert=True)
    
    # Revoke all
    count = await client.mongodb.revoke_all_access()
    
    await query.answer(f"✓ Revoked {count} access tokens!", show_alert=True)
    
    # Refresh the panel
    await access_token_panel(client, query)

#===============================================================#

@Client.on_message(filters.command('revoke_access') & filters.private)
async def revoke_access_command(client: Client, message):
    """Command to revoke a specific user's access"""
    if message.from_user.id not in client.admins:
        return await message.reply("❌ Only admins can use this!")
    
    if len(message.command) < 2:
        return await message.reply("**Usage:** `/revoke_access USER_ID`\n\nExample: `/revoke_access 123456789`")
    
    try:
        user_id = int(message.command[1])
        await client.mongodb.revoke_user_access(user_id)
        await message.reply(f"✓ **Access revoked for user** `{user_id}`")
    except ValueError:
        await message.reply("❌ Invalid user ID. Please provide a valid number.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


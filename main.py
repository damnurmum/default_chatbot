from bot_instance import bot # import bot var
from config import ADMIN # for init media file id
import handlers # import handlers for bot

from json import load, dump # for creating and reading media_ids.json
from os.path import exists # for checking file media_ids.json

if not exists("media_ids.json"):
    with open("media_ids.json", "w") as file:
        dump({"START_COMMAND_GIF": None, "COMMENT_GIF": None}, file)

with open("media_ids.json", "r+") as file:
    media_ids_json = load(file)

    updated = False

    if not media_ids_json["START_COMMAND_GIF"]:
        msg = bot.send_animation(ADMIN, open("resources/start_gif.mp4", "rb"), caption="ITS MESSAGE FOR GETTING ID OF MEDIA!!!")
        file_id = msg.animation.file_id
        media_ids_json["START_COMMAND_GIF"] = file_id
        updated = True

    if not media_ids_json["COMMENT_GIF"]:
        msg = bot.send_animation(ADMIN, open("resources/comment_gif.mp4", "rb"), caption="ITS MESSAGE FOR GETTING ID OF MEDIA!!!")
        file_id = msg.animation.file_id
        media_ids_json["COMMENT_GIF"] = file_id
        updated = True

    if updated:
        file.seek(0)
        dump(media_ids_json, file, indent=4)
        file.truncate()
        bot.send_message(ADMIN, "Success! Now bot is starting...")

# start bot
if __name__ == "__main__":
    bot.infinity_polling()
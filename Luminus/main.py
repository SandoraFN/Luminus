import requests
from PIL import Image
from io import BytesIO
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.media_group import MediaGroupBuilder
from datetime import datetime
import config
from aiogram.types import FSInputFile
import os
import asyncio
import pytz

def scan_shop():
    method = "get"
    url = "https://fortniteapi.io/v2/shop?lang=uk"
    header = {"Authorization": config.api_token}
    rsp = requests.request(method, url, headers=header)
    image_urls = []
    restricted_types = ["bandle", "sparks_song"]

    for element in rsp.json()["shop"]:
        if element["mainType"] not in restricted_types:
            if len(element["displayAssets"]) >= 1:
                image_urls.append(element["displayAssets"][0]['full_background'])

    grid_columns = 6
    grid_rows = 6
    padding = 15

    bg_width = 2415
    bg_height = 2700
    bg = Image.open('bg.png').resize((bg_width, bg_height), Image.LANCZOS)

    cell_width = (bg_width - (grid_columns + 1) * padding) // grid_columns
    cell_height = (bg_height - (grid_rows + 1) * padding) // grid_rows
    image_size = (cell_width, cell_height)

    x, y = padding, padding
    gi = 0

    for i, elem in enumerate(image_urls):
        try:
            response = requests.get(elem)
            image = Image.open(BytesIO(response.content)).resize(image_size, Image.LANCZOS)
            bg.paste(image, (x, y))

            if (i + 1) % grid_columns == 0:
                x = padding
                y += image_size[1] + padding
                if (i + 1) % (grid_columns * grid_rows) == 0:
                    bg.save(f'output/{gi}.png')
                    gi += 1
                    y = padding
                    bg = Image.open('bg.png').resize((bg_width, bg_height), Image.LANCZOS)
            else:
                x += image_size[0] + padding
        except Exception as e:
            print(f"Error processing image: {e}")

    bg.save(f'output/final.png')
    return True

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.TOKEN)
dp = Dispatcher()

@dp.message(Command("manual"))
async def test(message: types.Message):
    await message.answer("генерую пост (залежить від швидкості API)")
    scan_shop()
    dt = datetime.now(pytz.timezone('Europe/Kyiv')).strftime('%d:%m:%Y')
    album_builder = MediaGroupBuilder(
        caption=f"Дейлі апдейт магазину Fortnite\n🗓 {dt}\n\nUSE CODE LUMINUS"
    )
    for image in os.listdir("output"):
        album_builder.add_photo(
            type="photo",
            media=FSInputFile(f"output/{image}")
        )
    await message.answer_media_group(media=album_builder.build())
    for filename in os.listdir("output"):
        file_path = os.path.join("output", filename)
        os.remove(file_path)
        print(f"Файл {file_path} видалено.")

async def send_daily_message():
    while True:
        current_time = datetime.utcnow().time()
        if current_time.hour == 0 and current_time.minute == 1:
            await bot.send_message(5852385230, "started scheduled")
            print("Scheduled message was launched")
            scan_shop()
            dt = datetime.now(pytz.timezone('Europe/Kyiv')).strftime('%d:%m:%Y')
            album_builder = MediaGroupBuilder(
                caption=f"Дейлі апдейт магазину Fortnite\n🗓 {dt}\n\nUSE CODE LUMINUS"
            )
            for image in os.listdir("output"):
                album_builder.add_photo(
                    type="photo",
                    media=FSInputFile(f"output/{image}")
                )
            await bot.send_media_group(-1002115682668, media=album_builder.build())
            await bot.send_media_group(5852385230, media=album_builder.build())
            for filename in os.listdir("output"):
                file_path = os.path.join("output", filename)
                os.remove(file_path)
                print(f"Файл {file_path} видалено.")
        await asyncio.sleep(60)

async def main():
    asyncio.create_task(send_daily_message())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

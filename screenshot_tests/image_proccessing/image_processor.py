import logging
from io import BytesIO
from typing import Union, List

from PIL import ImageDraw, Image


class ImageProcessor(object):
    """Класс для обработки изображений (нарезки и сравнения)"""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    ALPHA = "alpha"

    # https://github.com/rsmbl/Resemble.js/blob/dec5ae1cf1d10c9027a94400a81c17d025a9d3b6/resemble.js#L121
    # https://github.com/rsmbl/Resemble.js/blob/dec5ae1cf1d10c9027a94400a81c17d025a9d3b6/resemble.js#L981
    tolerance = {
        RED: 32,
        GREEN: 32,
        BLUE: 32,
        ALPHA: 32,
    }

    def __init__(self):
        self._block_width = 40  # default
        self._block_height = 40

    def _slice_image(self, image: Image.Image) -> List[dict]:
        """Нарезать картинки на блоки"""
        max_width, max_height = image.size

        # нижний правый угол для кропа
        width_change = self._block_width
        height_change = self._block_height

        result = []
        for row in range(0, max_height, self._block_height):
            for col in range(0, max_width, self._block_width):
                # Если дошли до края изображения
                if width_change > max_width:
                    width_change = max_width
                # отрезаем по краю
                if height_change > max_height:
                    height_change = max_height

                # col, row -- верхний левый угол
                box = (col, row, width_change, height_change)
                cropped = image.crop(box)
                result.append({"image": cropped, "box": box})
                # сдвигаем вправо по ширине
                width_change += self._block_width

            # сдвигаем вниз по высоте
            height_change += self._block_height
            # возвращаем указатель на ширину в стартовую позицию
            width_change = self._block_width

        return result

    def _is_color_similar(self, a, b, color):
        """Проверить похожесть цветов. Для того, чтобы тесты не тригеррились на антиалиазинг допуски

        в self.tolerance.
        """
        if a is None and b is None:
            return True

        diff = abs(a - b)

        if diff == 0:
            return True
        elif diff < self.tolerance[color]:
            return True

        return False

    def _compare_images(self, image_one: Image.Image, image_two: Image.Image) -> bool:
        """Сравнить два изображения попиксельно"""
        assert image_one.size == image_two.size, \
            f"Картинки должны быть одинакового размера, {image_one.size} {image_two.size}"

        max_width, max_height = image_one.size

        for coord_y in range(0, max_height):
            for coord_x in range(0, max_width):
                pixel_one = image_one.getpixel((coord_x, coord_y))
                pixel_two = image_two.getpixel((coord_x, coord_y))
                equal = self._compare_pixels(pixel_one, pixel_two)
                if not equal:
                    return False

        return True

    def _compare_pixels(self, pixel_one, pixel_two) -> bool:
        """Сравнить каждый цвет, каждого писклея."""
        assert len(pixel_one) == len(pixel_two), f"В одном из пикселей не хватает цветов: {pixel_one} {pixel_two}"

        for item in zip(pixel_one, pixel_two, (self.RED, self.GREEN, self.BLUE, self.ALPHA)):
            color_one, color_two, color = item
            if not self._is_color_similar(color_one, color_two, color):
                return False

        return True

    def get_images_diff(self, first_image: Image.Image, second_image: Image.Image) -> List[Union[int, bytes]]:
        """Поблочно сравнить два изображения и вернуть количество блоков с несовпавшими пикселями"""
        result_image = first_image.copy()

        first_image_blocks = self._slice_image(first_image)
        second_image_blocks = self._slice_image(second_image)

        # если скриншоты разных размеров, то все блоки из большего скриншота, которые не попали в меньший нужно добавить
        # к битым
        mistaken_blocks = abs(len(first_image_blocks) - len(second_image_blocks))

        for index in range(min(len(first_image_blocks), len(second_image_blocks))):
            image_equal = self._compare_images(first_image_blocks[index]["image"], second_image_blocks[index]["image"])

            if not image_equal:
                draw = ImageDraw.Draw(result_image)
                draw.rectangle(first_image_blocks[index]["box"], outline="red")
                mistaken_blocks += 1

        return [mistaken_blocks, self.image_to_bytes(result_image)]

    def paste(self, screenshots: List[bytes], over_height: int) -> Image.Image:
        """Склеить массив скриншотов в одно изображение"""
        max_width = 0
        max_height = 0
        images = []

        for screenshot in screenshots:
            image = self.load_image_from_bytes(screenshot)
            images.append(image)
            max_width = image.size[0] if image.size[0] > max_width else max_width
            max_height += image.size[1]

        # Склейка работает так: сначала создаем одно "пустое" изображение равное размеру всех скелееных, и вставляем в
        # в него по одному все скриншоты.
        # Чтобы в финальном скрине не получилось что скриншоты заняли меньше места, чем картинка, снизу отрезаем over_height
        max_height = max_height - over_height
        result = Image.new('RGB', (max_width, max_height))
        logging.info(f'Screen size: ({max_width}, {max_height})')

        offset = 0
        last_image_index = len(images) - 1
        for index, image in enumerate(images):
            # Расскоментить если нужно посмотреть какие скрины склеиваются в один
            # with open(f"screen-{index}.png", "wb") as fp:
            #     image.save(fp)

            if last_image_index == index and over_height != 0:
                # с последнего скриншота срезаем ту часть, в которой он дублирует предпоследний
                logging.info(f"Crop over height: {over_height}")
                image = image.crop((0, over_height, image.size[0], image.size[1]))

            result.paste(image, (0, offset))
            logging.info(f"Image added, offset is {offset}")
            offset += image.size[1]

        return result

    def load_image_from_bytes(self, data: bytes) -> Image.Image:
        """Загрузить изображение из байтовой строки."""
        with BytesIO(data) as fp:
            image: Image.Image = Image.open(fp)
            image.load()
            return image

    def image_to_bytes(self, image: Image.Image) -> bytes:
        with BytesIO() as fp:
            image.save(fp, "PNG")
            return fp.getvalue()

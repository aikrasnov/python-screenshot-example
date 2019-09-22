from PIL import ImageDraw, Image
from io import BytesIO
from typing import Tuple, List

import logging


class ImageProcessor(object):
    """Class for image comparison."""

    def __init__(self):
        self._block_width = 20  # default
        self._block_height = 20
        self._accuracy = 0.0001  # less better

    def _slice_image(self, image: Image.Image) -> List[dict]:
        """Slice image on small blocks."""
        max_width, max_height = image.size

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

    def _get_image_pixel_sum(self, image: Image.Image) -> int:
        """Get pixel sum for image."""
        image_total = 0
        max_width, max_height = image.size

        for coord_y in range(0, max_height):
            for coord_x in range(0, max_width):
                pixel = image.getpixel((coord_x, coord_y))
                image_total += sum(pixel)

        return image_total

    def get_images_diff(self, first_image: Image.Image, second_image: Image.Image) -> Tuple[int, bytes, bytes, bytes]:
        """Compare two images."""
        result_image = first_image.copy()

        first_image_blocks = self._slice_image(first_image)
        second_image_blocks = self._slice_image(second_image)

        # если скриншоты разных размеров, то все блоки из большего скриншота, которые не попали в меньший нужно добавить
        # к битым
        mistaken_blocks = abs(len(first_image_blocks) - len(second_image_blocks))

        for index in range(min(len(first_image_blocks), len(second_image_blocks))):
            first_pixels = self._get_image_pixel_sum(first_image_blocks[index]["image"])
            second_pixels = self._get_image_pixel_sum(second_image_blocks[index]["image"])

            # если пиксели отличаются больше чем на self.accuracy -- помечаем блок как битый
            if (first_pixels != 0 and second_pixels != 0) and abs(1 - (first_pixels / second_pixels)) >= self._accuracy:
                draw = ImageDraw.Draw(result_image)
                draw.rectangle(first_image_blocks[index]["box"], outline="red")
                mistaken_blocks += 1

        result = BytesIO()
        first = BytesIO()
        second = BytesIO()

        result_image.save(result, 'PNG')
        first_image.save(first, 'PNG')
        second_image.save(second, 'PNG')

        return mistaken_blocks, result.getvalue(), first.getvalue(), second.getvalue()

    def paste(self, screenshots: List[bytes]) -> Image.Image:
        """Concatenate few images into one."""
        max_width = 0
        max_height = 0
        images = []
        for screenshot in screenshots:
            image = self.load_image_from_bytes(screenshot)
            images.append(image)
            max_width = image.size[0] if image.size[0] > max_width else max_width
            max_height += image.size[1]
        result = Image.new('RGB', (max_width, max_height))
        logging.info(f'Screen size: ({max_width}, {max_height})')
        offset = 0
        for image in images:
            result.paste(image, (0, offset))
            logging.info(f"Image added, offset is {offset}")
            offset += image.size[1]

        return result

    def load_image_from_bytes(self, data: bytes):
        """Загрузить изображение из байтовой строки."""
        return Image.open(BytesIO(data))

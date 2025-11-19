from io import BytesIO
from tkinter import Tk, Label, Frame, Button
from typing import List, Tuple, Optional
from PIL import Image
from PIL.ImageFile import ImageFile
from PIL.ImageTk import PhotoImage
from api.repositories.sudoku_repository import SudokuRepository

class SudokuImageViewer:
    def __init__(self) -> None:
        self.__root: Tk = Tk()
        self.__root.title("Sudoku Image Viewer")
        self.__description_label: Optional[Label] = None
        self.__image_label: Optional[Label] = None
        self.__counter_label: Optional[Label] = None
        self.__image: Optional[PhotoImage] = None

        self.__images: List[Tuple[str, ImageFile]] = []
        self.__current_index: int = 0
        self.__load_images()
        self.__load_ui()

    def view(self) -> None:
        self.__display_image()
        self.__root.mainloop()

    def __display_image(self) -> None:
        image_description, image = self.__images[self.__current_index]
        image = image.copy()
        image.thumbnail((750, 750))

        self.__image = PhotoImage(image)
        self.__image_label.config(image=self.__image)
        self.__description_label.config(text=image_description)
        self.__counter_label.config(text=f"{self.__current_index + 1} / {len(self.__images)}")

    def __next(self) -> None:
        self.__current_index = (self.__current_index + 1) % len(self.__images)
        self.__display_image()

    def __previous(self) -> None:
        self.__current_index = (self.__current_index - 1) % len(self.__images)
        self.__display_image()

    def __load_images(self) -> None:
        for sudoku in SudokuRepository.get_all(has_images=True):
            for image in sudoku.images:
                pil_image = Image.open(BytesIO(image.content))
                self.__images.append((f"{sudoku.candidate_type.name} {sudoku.n}x{sudoku.n}", pil_image))
        assert len(self.__images) > 0, "No images were found in the database"

    def __load_ui(self) -> None:
        # Description
        self.__description_label = Label(self.__root, anchor="center", justify="center")
        self.__description_label.pack(fill="x")

        # Image
        self.__image_label = Label(self.__root)
        self.__image_label.pack()

        # Navigation
        btn_frame: Frame = Frame(self.__root)
        btn_frame.pack(fill="x")

        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)

        Button(btn_frame, text="Previous", command=self.__previous).grid(row=0, column=0, sticky="nsew")
        self.__counter_label = Label(btn_frame, anchor="center")
        self.__counter_label.grid(row=0, column=1, sticky="nsew")
        Button(btn_frame, text="Next", command=self.__next).grid(row=0, column=2, sticky="nsew")

def main() -> None:
    SudokuImageViewer().view()

if __name__ == "__main__":
    main()

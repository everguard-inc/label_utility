import argparse
import json
import os
import sys
from copy import copy, deepcopy
from typing import Union, List, Dict

import cv2
import numpy as np

import config as cfg
from data_structures import BBox, Annotation, Point


class Canvas:
    """Works with graphics"""

    def __init__(self):
        self._bboxes: List[BBox]
        self._current_image: np.ndarray
        self._mode: cfg.LabelingMode = cfg.LabelingMode.DRAWING
        self._clear_image: np.ndarray
        self._selected_class_label: cfg.ClassLabel = cfg.DEFAULT_CLASS_LABEL
        cv2.namedWindow(cfg.WINDOW_NAME, cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
        cv2.setMouseCallback(cfg.WINDOW_NAME, self._on_mouse)
        cv2.resizeWindow(cfg.WINDOW_NAME, 900, 600)

    def set_mode(self, mode: cfg.LabelingMode):
        self._mode = mode

    def set_image(self, img: np.ndarray):
        self._clear_image = img

    def refresh(self):
        self._render_bboxes(self._bboxes)

    def set_class_label(self, class_label: cfg.ClassLabel):
        self._selected_class_label = class_label

    def get_bboxes_json(self):
        bboxes_list = list()
        for bbox in self._bboxes:
            bboxes_list.append(
                [bbox.x1, bbox.y1, bbox.x2, bbox.y2, cfg.LABEL_CATEGORY_ID[bbox.label]]
            )
        return bboxes_list

    def set_bboxes(self, bboxes):
        self._bboxes = deepcopy(bboxes)

    def draw_bbox(self):
        region = cv2.selectROI(cfg.WINDOW_NAME, self._current_image)
        cv2.setMouseCallback(cfg.WINDOW_NAME, self._on_mouse)

        y1 = int(region[1])
        y2 = int(region[1] + region[3])
        x1 = int(region[0])
        x2 = int(region[0] + region[2])

        self._bboxes.append(BBox(x1, y1, x2, y2, self._selected_class_label))
        print(f"bbox with class {self._selected_class_label} created")

        self.refresh()

    def _on_mouse(self, event, x, y, flags, param):
        point = Point(x, y)
        if event == cv2.EVENT_LBUTTONDOWN:
            if self._mode == cfg.LabelingMode.DELETION:
                self._delete_bbox(point)
            if self._mode == cfg.LabelingMode.SET_LABEL:
                self._set_label(point)

            self.refresh()

    def _delete_bbox(self, point: Point):
        bbox_id = self._get_selected_bbox_id(point)
        if bbox_id is not None:
            print(f"bbox with id {bbox_id} deleted")
            del self._bboxes[bbox_id]

    def _set_label(self, point: Point):
        bbox_id = self._get_selected_bbox_id(point)
        if bbox_id is not None:
            self._bboxes[bbox_id].label = self._selected_class_label
            print(f"set label {self._selected_class_label} for bbox with id {bbox_id}")

    def _get_selected_bbox_id(self, point: Point) -> Union[int, None]:
        idx = None
        for i, bbox in enumerate(self._bboxes):
            if point in bbox:
                idx = i
                break

        return idx

    def _render_bboxes(self, bboxes: List[BBox], show_id=False):
        self._current_image = self._clear_image.copy()

        for i, bbox in enumerate(bboxes):
            cv2.rectangle(
                self._current_image,
                (bbox.x1, bbox.y1),
                (bbox.x2, bbox.y2),
                cfg.CLASS_COLORS[bbox.label],
                cfg.DEFAULT_BBOX_LINE_THICKNESS,
            )

            if show_id:
                self._current_image = cv2.putText(
                    self._current_image,
                    str(i),
                    (bbox.x1, bbox.y1),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    self._current_image.shape[0] * cfg.TEXTSIZE_IM_WIDTH_RATIO,
                    cfg.TEXT_COLOR,
                    int(
                        self._current_image.shape[0] * cfg.TEXTTHICKNESS_IM_WIDTH_RATIO
                    ),
                    cv2.LINE_AA,
                )

        cv2.imshow(cfg.WINDOW_NAME, self._current_image)


class LabelingTool:
    """Connects user with canvas"""

    def __init__(self, annotations: str, output_folder: str, image_folder: str):
        self._images_folder: str = image_folder
        self._output_folder: str = output_folder
        self._canvas: Canvas = Canvas()
        self._source_annotations: Annotation = self._open_annotations(annotations)
        self._skip_indices: List[int] = self._get_skip_image_list()
        self._current_image_id = self._get_nearest_unlabeled_image_id(0)
        self._running: bool = True
        self._reload_canvas()
        self._run_event_loop()

    def _run_event_loop(self):
        while self._running:
            k = cv2.waitKey()
            if k == cfg.HotKey.SetDrawMode:
                print("drawing mode is set")
                self._canvas.draw_bbox()
            elif k == cfg.HotKey.SetDeletionMode:
                self._canvas.set_mode(cfg.LabelingMode.DELETION)
                print("delete mode is set")
            elif k == cfg.HotKey.SetModeChangeName:
                self._canvas.set_mode(cfg.LabelingMode.SET_LABEL)
                print("name changing mode is set")
            elif k == cfg.HotKey.SkipImage:
                self._skip_image()
                print(
                    f"image {self._source_annotations.get_image_name_by_id(self._current_image_id)} skipped"
                )
            elif k == cfg.HotKey.UndoLabeling:
                self._undo_changes()
                print("changes reverted")
            elif k == cfg.HotKey.SaveAndOpenNext:
                self._save_and_open_next()
                print(
                    f"opened image {self._source_annotations.get_image_name_by_id(self._current_image_id)}"
                )
            elif k == cfg.HotKey.Quit:
                print("exiting")
                self._quit()

            for key, class_label in cfg.ClassHotKeys.items():
                if k == key:
                    print(f"selected class {class_label}")
                    self._update_canvas_label(class_label)

    def _update_canvas_label(self, class_label: cfg.ClassLabel):
        self._canvas.set_class_label(class_label)

    def _save_and_open_next(self):
        self._save()
        self._iterate(True, 1)

    def _skip_image(self):
        self._iterate(True, 1)

    def _undo_changes(self):
        self._set_current_bboxes_to_canvas()
        self._reload_canvas()

    def _open_annotations(self, annotation_path):
        ann = Annotation()
        ann.open_coco_annotation(annotation_path)
        return ann

    def _get_nearest_unlabeled_image_id(self, image_id: int) -> int:
        while image_id in self._skip_indices:
            image_id += 1
        return image_id

    def _update_current_image_id(self, direction: bool, step: int):
        new_image_id = (
            self._current_image_id + step
            if direction
            else self._current_image_id - step
        )

        new_image_id = self._get_nearest_unlabeled_image_id(new_image_id)

        if new_image_id > self._source_annotations.images_amount:
            new_image_id = self._source_annotations.images_amount - 1
        elif new_image_id < 0:
            new_image_id = 0
        self._current_image_id = new_image_id

    def _get_skip_image_list(self) -> List[int]:
        labeled_images_names = os.listdir(self._output_folder)
        images_in_annotation = self._source_annotations.get_sorted_images_names()

        labeled_base_names = [
            os.path.splitext(name)[0] for name in labeled_images_names
        ]
        source_base_names = [
            os.path.splitext(name)[0] for name in images_in_annotation
        ]

        # collect image indices which are present both in annotation and output folder
        skip_indices = list()
        for i, image_name in enumerate(source_base_names):
            if image_name in labeled_base_names:
                skip_indices.append(i)

        print('skip', skip_indices)

        return skip_indices

    def _set_current_bboxes_to_canvas(self):
        self._canvas.set_bboxes(
            self._source_annotations.get_bboxes_for_image(self._current_image_id)
        )

    def _set_current_image_to_canvas(self):
        img_name = self._source_annotations.get_image_name_by_id(self._current_image_id)
        img_path = os.path.join(self._images_folder, img_name)
        img = cv2.imread(img_path)
        self._canvas.set_image(img)

    def _reload_canvas(self):
        self._set_current_bboxes_to_canvas()
        self._set_current_image_to_canvas()
        self._canvas.refresh()
        image_name = self._source_annotations.get_image_name_by_id(self._current_image_id)
        print(f'image id: {self._current_image_id}, image name: {image_name}')

    def _iterate(self, direction: bool, step: int):
        self._update_current_image_id(direction, step)
        self._reload_canvas()

    def _save(self):
        json_bboxes = self._canvas.get_bboxes_json()
        img_name = self._source_annotations.get_image_name_by_id(self._current_image_id)
        base_img_name, ext = os.path.splitext(img_name)
        output_ann_path = os.path.join(self._output_folder, f"{base_img_name}.txt")
        with open(output_ann_path, "w") as output_file:
            json.dump(json_bboxes, output_file)

    def _quit(self):
        cv2.destroyAllWindows()
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_coco")
    parser.add_argument("--output_folder")
    parser.add_argument("--images")
    args = parser.parse_args()

    ltool = LabelingTool(args.input_coco, args.output_folder, args.images)

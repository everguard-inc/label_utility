import argparse
import json
import os
import sys
from copy import deepcopy

from typing import Union, List, Dict

import cv2
import numpy as np

import config as cfg
from data_structures import BBox, Annotation, Point
from utils import Canvas


class LabelingTool:
    """Connects user with canvas"""

    def __init__(self, annotations: str, output_folder: str, image_folder: str, start_frame_id: str=None):
        self._images_folder: str = image_folder
        self._output_folder: str = output_folder
        self._dir_skipped = os.path.join(self._output_folder, cfg.DIRECTORY_FOR_SKIPPED_NAME)
        self._dir_labeled = os.path.join(self._output_folder, cfg.DIRECTORY_FOR_LABELED_NAME)
        self._create_directories()
        self._canvas: Canvas = Canvas()
        self._source_annotations: Annotation = self._open_annotations(annotations)
        self._skip_indices: List[int] = list()
        if start_frame_id is None:
            self._skip_indices = self._get_skip_image_list()
        self._current_image_id: int = self._set_start_frame_id(start_frame_id)
        self._running: bool = True
        self._reload_canvas()
        self._run_event_loop()

    def _set_start_frame_id(self, frame_id: Union[int, str]):
        if frame_id is not None:
            frame_id = int(frame_id)
            if 0 <= frame_id < self._source_annotations.images_amount:
                return frame_id
        else:
            return self._get_nearest_unlabeled_image_id(0)

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
                print(
                    f"image id: {self._current_image_id}, image name: {self._source_annotations.get_image_name_by_id(self._current_image_id)} skipped"
                )
                self._skip_image()
            elif k == cfg.HotKey.UndoLabeling:
                self._undo_changes()
                print("changes reverted")
            elif k == cfg.HotKey.SaveAndOpenNext:
                self._save_and_open_next()
                print(f'image id: {self._current_image_id}, image name: {self._source_annotations.get_image_name_by_id(self._current_image_id)} saved')
            elif k == cfg.HotKey.Quit:
                print("exiting")
                self._quit()

            if self._canvas.state == cfg.CanvasState.NORMAL:
                for key, class_label in cfg.ClassHotKeys.items():
                    if k == key:
                        print(f"selected class {class_label}")
                        self._update_canvas_label(class_label)

            elif self._canvas.state == cfg.CanvasState.ASK_BBOX_INDEX:
                for key, number_value in cfg.NumberHotKeys.items():
                    if k == key:
                        print(f"selected bbox id {number_value}")
                        self._canvas.change_bbox_by_id(number_value)

    def _create_directories(self):
        if not os.path.exists(self._dir_skipped):
            os.makedirs(self._dir_skipped)
        if not os.path.exists(self._dir_labeled):
            os.makedirs(self._dir_labeled)

    def _update_canvas_label(self, class_label: cfg.ClassLabel):
        self._canvas.set_class_label(class_label)

    def _save_and_open_next(self):
        self._save(self._dir_labeled)
        self._iterate(True, 1)

    def _skip_image(self):
        self._save(self._dir_skipped)
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
        labeled_images_names = os.listdir(self._dir_labeled)
        skipped_images_names = os.listdir(self._dir_skipped)
        completed_images_names = labeled_images_names + skipped_images_names

        images_in_annotation = self._source_annotations.get_sorted_images_names()

        completed_base_names = [
            os.path.splitext(name)[0] for name in completed_images_names
        ]
        source_base_names = [
            os.path.splitext(name)[0] for name in images_in_annotation
        ]

        # collect image indices which are present both in annotation and output folder
        skip_indices = list()
        for i, image_name in enumerate(source_base_names):
            if image_name in completed_base_names:
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

    def _iterate(self, direction: bool, step: int):
        self._update_current_image_id(direction, step)
        self._reload_canvas()

    def _save(self, dir_path: str):
        json_bboxes = self._canvas.get_bboxes_json()
        img_name = self._source_annotations.get_image_name_by_id(self._current_image_id)
        base_img_name, ext = os.path.splitext(img_name)
        output_ann_path = os.path.join(dir_path, f"{base_img_name}.txt")
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
    parser.add_argument("--start_frame_id")
    args = parser.parse_args()

    ltool = LabelingTool(args.input_coco, args.output_folder, args.images, args.start_frame_id)

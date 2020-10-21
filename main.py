import argparse
import json
import os
import sys
from copy import deepcopy

from typing import Union, List, Dict

import cv2
import numpy as np

import config as cfg
from data_structures import BBox, Point
from utils import Canvas, AnnotationStorage


class LabelingTool:
    """Connects user with canvas"""

    def __init__(self, annotation_path: str, output_folder: str, image_folder: str, start_frame_id: str=None):
        self._images_folder: str = image_folder
        self._dir_skipped = os.path.join(output_folder, cfg.DIRECTORY_FOR_SKIPPED_NAME)
        self._dir_labeled = os.path.join(output_folder, cfg.DIRECTORY_FOR_LABELED_NAME)
        self._create_directories()
        self._canvas: Canvas = Canvas()
        self._annotations: AnnotationStorage = AnnotationStorage(annotation_path,
                                                                 output_folder,
                                                                 image_folder,
                                                                 start_frame_id)
        self._running: bool = True
        self._reload_canvas()
        self._run_event_loop()

    def _run_event_loop(self):
        while self._running:
            k = cv2.waitKey()
            if k == cfg.HotKey.SetDrawMode:
                print("draw bbox")
                self._canvas.draw_bbox()
            elif k == cfg.HotKey.SetDeletionMode:
                self._canvas.set_mode(cfg.LabelingMode.DELETION)
                print("delete mode is set")
            elif k == cfg.HotKey.SetModeChangeName:
                self._canvas.set_mode(cfg.LabelingMode.SET_LABEL)
                print("name changing mode is set")
            elif k == cfg.HotKey.MarkSkipped:
                self._mark_as_skiped()
            elif k == cfg.HotKey.UndoLabeling:
                self._undo_changes()
            elif k == cfg.HotKey.SaveAndOpenNext:
                self._save_and_open_next()
                print(f'image id: {self._current_image_id}, image name: {self._source_annotations.get_image_name_by_id(self._current_image_id)} saved')
            elif k == cfg.HotKey.Quit:
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
                        self._canvas.specify_bbox(number_value)

    def _create_directories(self):
        if not os.path.exists(self._dir_skipped):
            os.makedirs(self._dir_skipped)
        if not os.path.exists(self._dir_labeled):
            os.makedirs(self._dir_labeled)

    def _update_canvas_label(self, class_label: cfg.ClassLabel):
        self._canvas.set_class_label(class_label)

    def _save_and_open_next(self):
        self._save(self._dir_labeled)
        img_name = self._annotations.current_image_name
        img_id = self._annotations.current_image_id
        print(f"image id: {img_id}, image name: {img_name} annotation saved in labeled folder")

        self._iterate(True, 1)

    def _mark_as_skiped(self):
        self._save(self._dir_skipped)
        img_name = self._annotations.current_image_name
        img_id = self._annotations.current_image_id
        print(f"image id: {img_id}, image name: {img_name} annotation saved in skipped folder")

        self._iterate(True, 1)

    def _undo_changes(self):
        self._set_current_bboxes_to_canvas()
        self._reload_canvas()
        print("changes reverted")

    def _set_current_bboxes_to_canvas(self):
        self._canvas.set_bboxes(self._annotations.current_bboxes)

    def _set_current_image_to_canvas(self):
        img_name = self._annotations.current_image_name
        img_path = os.path.join(self._images_folder, img_name)
        img = cv2.imread(img_path)
        self._canvas.set_image(img)

    def _reload_canvas(self):
        self._set_current_bboxes_to_canvas()
        self._set_current_image_to_canvas()
        self._canvas.refresh()

    def _iterate(self, direction: bool, step: int):
        self._annotations.change_current_image_id(direction, step)
        self._reload_canvas()
        img_name = self._annotations.current_image_name
        img_id = self._annotations.current_image_id
        print(f"image id: {img_id}, image name: {img_name} opened")

    def _save(self, dir_path: str):
        json_bboxes = self._canvas.get_bboxes_json()
        img_name = self._annotations.current_image_name
        base_img_name, ext = os.path.splitext(img_name)
        output_ann_path = os.path.join(dir_path, f"{base_img_name}.txt")
        with open(output_ann_path, "w") as output_file:
            json.dump(json_bboxes, output_file)

    def _quit(self):
        cv2.destroyAllWindows()
        print("exiting")
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_coco")
    parser.add_argument("--output_folder")
    parser.add_argument("--images")
    parser.add_argument("--start_frame_id")
    args = parser.parse_args()

    ltool = LabelingTool(args.input_coco, args.output_folder, args.images, args.start_frame_id)

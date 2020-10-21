# label_utility

#### Run
```
python main.py [--input_coco INPUT_COCO] [--output_folder OUTPUT_FOLDER]
               [--images IMAGES] [--start_frame_id START_FRAME_ID]

optional arguments:
  --input_coco INPUT_COCO           path to json with annotations in COCO format
  --output_folder OUTPUT_FOLDER     directory to save corrected annotations
  --images IMAGES                   directory with images
  --start_frame_id START_FRAME_ID   frame number from which to start labeling
```

#### Control keys
| Key | Action | 
| --- | --- |
| Y  | Save and open next image | 
| N  | Mark image as skipped and open next image | 
| X  | Open next image without saving | 
| Z  | Open previous image without saving | 
| R  | Undo | 
| W  | Draw bbox |
| D  | Delete mode |
| I  | Renaming mode | 
| Q  | Quit | 


#### Classes keys
| Key | Class | 
| --- | --- |
| 0  | person | 
| 1  | with_helmet | 
| 2  | with_vest | 
| 3  | with_vest_and_helmet | 
| 4  | invisible_without_vest |
| 5  | invisible_with_vest |


#### Create bbox
1. Select a class by pressing the class hotkey or leave the class you selected earlier. The class name will be displayed on the command line
2. Press W
3. Draw ROI. You can draw it several times until it is positioned as you want. Each time the previously drawn bbox will be removed.
4. When done - press space

#### Rename bbox
1. Press I
2. Press the hotkey of the class you want
3. Click on bbox you want to rename

#### Delete bbox
1. Press D
2. Left click on bbox

#### Select overlapping bboxes
When you click a point that is included in more than one bbox, then you need to indicate from the keyboard which bbox was selected.
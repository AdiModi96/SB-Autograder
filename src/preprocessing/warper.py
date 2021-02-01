import os

import cv2
import numpy as np
from cv2 import aruco
from tqdm import tqdm

from src import paths


class PerspectiveWarper:
    def __init__(self):
        self.output_folder_path = os.path.join(paths.data_folder_path, 'preprocessed', 'warped')
        if not os.path.isdir(self.output_folder_path):
            os.makedirs(self.output_folder_path)

    def find_anchor_points(self, image):
        aruco_dict = aruco.Dictionary_get(aruco.DICT_7X7_1000)
        aruco_params = aruco.DetectorParameters_create()
        corners, ids, rejected = aruco.detectMarkers(image, aruco_dict, parameters=aruco_params)
        anchor_points = []
        for corner in corners:
            center = np.mean(corner, axis=1)[0]
            anchor_points.append([center[0], center[1]])

        if len(anchor_points) == 4:
            _, anchor_points = zip(*sorted(zip(ids, anchor_points), key=lambda element: element[0]))

        return anchor_points

    def warp_shallow(self, video_file_path, frame_size):

        if not os.path.exists(video_file_path):
            print('Quitting: Video path does not exits')
            return

        video = cv2.VideoCapture(video_file_path)
        num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video.get(cv2.CAP_PROP_FPS)

        anchor_points_found = False
        warping_matrix = None

        print('Searching frame with anchor points ...')
        progress_bar = tqdm(total=num_frames, unit=' frames')
        for frame_idx in range(num_frames):
            _, frame = video.read()

            anchor_points = np.array(self.find_anchor_points(frame), dtype=np.float32)
            if len(anchor_points) == 4:
                anchor_points_found = True

                warped_anchor_points = np.array(
                    [
                        (frame_size[0], 0),
                        (0, 0),
                        (0, frame_size[1]),
                        (frame_size[0], frame_size[1]),
                    ],
                    dtype=np.float32
                )

                warping_matrix = cv2.getPerspectiveTransform(
                    anchor_points,
                    warped_anchor_points
                )
                progress_bar.update(num_frames)
                break

            progress_bar.update(1)
        progress_bar.close()
        video.set(cv2.CAP_PROP_POS_FRAMES, 0)

        if not anchor_points_found:
            print('Quitting: Anchor points not found')
            return

        print('Anchor points found')

        video_file_name = os.path.basename(video_file_path)

        video_writer = cv2.VideoWriter(
            os.path.join(self.output_folder_path, video_file_name),
            cv2.VideoWriter_fourcc(*'mp4v'),
            fps,
            frame_size
        )
        print('Warping ...')
        progress_bar = tqdm(total=num_frames, unit=' frames')
        for frame_idx in range(num_frames):
            _, frame = video.read()

            frame = cv2.warpPerspective(frame, warping_matrix, dsize=frame_size)
            video_writer.write(frame)
            progress_bar.update(1)

        video_writer.release()
        progress_bar.close()

    def warp_deep(self, video_file_path, frame_size):

        if not os.path.exists(video_file_path):
            print('Quitting: Video path does not exits')
            return

        video = cv2.VideoCapture(video_file_path)
        num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video.get(cv2.CAP_PROP_FPS)

        video_anchor_points = np.ndarray(shape=(num_frames, 4, 2), dtype=np.float32)
        anchor_points_found = True

        print('Searching frames for anchor points ...')
        progress_bar = tqdm(total=num_frames, unit=' frames')
        for frame_idx in range(num_frames):
            _, frame = video.read()

            anchor_points = np.array(self.find_anchor_points(frame), dtype=np.float32)
            if len(anchor_points) == 4:
                video_anchor_points[frame_idx] = np.asarray(anchor_points)
            else:
                anchor_points_found = False
                break
            progress_bar.update(1)
        progress_bar.close()
        video.set(cv2.CAP_PROP_POS_FRAMES, 0)

        if not anchor_points_found:
            print('Quitting: Anchor points not found')
            return

        print('Anchor points found')

        video_file_name = os.path.basename(video_file_path)

        video_writer = cv2.VideoWriter(
            os.path.join(self.output_folder_path, video_file_name),
            cv2.VideoWriter_fourcc(*'mp4v'),
            fps,
            frame_size
        )
        print('Warping ...')
        progress_bar = tqdm(total=num_frames, unit=' frames')
        for frame_idx in range(num_frames):
            _, frame = video.read()

            warped_anchor_points = np.array(
                [
                    (frame_size[0], 0),
                    (0, 0),
                    (0, frame_size[1]),
                    (frame_size[0], frame_size[1]),
                ],
                dtype=np.float32
            )

            warping_matrix = cv2.getPerspectiveTransform(
                video_anchor_points[frame_idx],
                warped_anchor_points
            )

            frame = cv2.warpPerspective(frame, warping_matrix, dsize=frame_size)
            video_writer.write(frame)
            progress_bar.update(1)

        progress_bar.close()
        video_writer.release()


warp = PerspectiveWarper()
video_file_path = os.path.abspath(os.path.join(paths.data_folder_path, 'raw', '77_bonus.mp4'))
frame_size = (720, 720)
warp.warp_shallow(video_file_path, frame_size)

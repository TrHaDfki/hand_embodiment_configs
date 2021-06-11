import yaml
import numpy as np
from mocap import qualisys, pandas_utils, conversion
from mocap.cleaning import median_filter, interpolate_nan


class HandMotionCaptureDataset:
    """Hand motion capture dataset.

    Parameters
    ----------
    filename : str
        Name of the qualisys file (.tsv).

    finger_names : list of str, optional (default: None)
        Names of tracked fingers.

    hand_marker_names : list of str, optional (default: None)
        Names of hand markers that will be used to find the hand's pose.

    finger_marker_names : dict, optional (default: None)
        Mapping from finger names to corresponding marker.

    additional_markers : list, optional (default: [])
        Additional markers that have been tracked.

    mocap_config : str, optional (default: None)
        Path to configuration file that contains finger names, hand marker,
        names, finger marker names, and additional markers.

    skip_frames : int, optional (default: 1)
        Skip this number of frames when loading the motion capture data.

    start_idx : int, optional (default: None)
        Index of the first valid sample.

    end_idx : int, optional (default: None)
        Index of the last valid sample.
    """
    def __init__(self, filename, mocap_config=None, skip_frames=1,
                 start_idx=None, end_idx=None, **kwargs):
        trajectory = qualisys.read_qualisys_tsv(filename=filename)

        if mocap_config is not None:
            with open(mocap_config, "r") as f:
                config = yaml.safe_load(f)
        else:
            config = dict()
        config.update(kwargs)

        marker_names = (config["hand_marker_names"] + list(config["finger_marker_names"].values())
                        + config.get("additional_markers", []))
        trajectory = pandas_utils.extract_markers(
            trajectory, marker_names).copy()
        trajectory = self._convert_zeros_to_nans(trajectory, marker_names)
        trajectory = trajectory.iloc[slice(start_idx, end_idx)]
        trajectory = trajectory.iloc[::skip_frames]
        trajectory = median_filter(interpolate_nan(trajectory), 3).iloc[2:]

        self.n_steps = len(trajectory)

        self._hand_trajectories(config["hand_marker_names"], trajectory)
        self._finger_trajectories(config["finger_marker_names"], config["finger_names"], trajectory)
        self._additional_trajectories(config.get("additional_markers", ()), trajectory)

    def _convert_zeros_to_nans(self, hand_trajectory, marker_names):
        column_names = pandas_utils.match_columns(
            hand_trajectory, marker_names, keep_time=False)
        for column_name in column_names:
            hand_trajectory[column_name].replace(0.0, np.nan, inplace=True)
        return hand_trajectory

    def _hand_trajectories(self, hand_marker_names, trajectory):
        self.hand_trajectories = []
        for marker_name in hand_marker_names:
            hand_column_names = pandas_utils.match_columns(
                trajectory, [marker_name], keep_time=False)
            hand_marker_trajectory = conversion.array_from_dataframe(
                trajectory, hand_column_names)
            self.hand_trajectories.append(hand_marker_trajectory)

    def _finger_trajectories(self, finger_marker_names, finger_names, trajectory):
        self.finger_trajectories = {}
        for finger_name in finger_names:
            finger_marker_name = finger_marker_names[finger_name]
            finger_column_names = pandas_utils.match_columns(
                trajectory, [finger_marker_name], keep_time=False)
            self.finger_trajectories[finger_name] = \
                conversion.array_from_dataframe(
                    trajectory, finger_column_names)

    def _additional_trajectories(self, additional_markers, trajectory):
        self.additional_trajectories = []
        for marker_name in additional_markers:
            column_names = pandas_utils.match_columns(
                trajectory, [marker_name], keep_time=False)
            additional_trajectory = conversion.array_from_dataframe(
                trajectory, column_names)
            self.additional_trajectories.append(additional_trajectory)

    def get_hand_markers(self, t):
        """Get hand markers to extract pose of the hand."""
        return [ht[t] for ht in self.hand_trajectories]

    def get_finger_markers(self, t):
        """Get finger markers."""
        return {fn: self.finger_trajectories[fn][t]
                for fn in self.finger_trajectories}

    def get_additional_markers(self, t):
        """Get additional markers."""
        return [at[t] for at in self.additional_trajectories]

    def get_markers(self, t):
        """Get positions of all markers."""
        hand_markers = self.get_hand_markers(t)
        finger_markers = self.get_finger_markers(t)
        additional_trajectories = self.get_additional_markers(t)
        return np.array(hand_markers + additional_trajectories + list(finger_markers.values()))

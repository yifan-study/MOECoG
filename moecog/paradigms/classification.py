"""Epoched classification paradigms for cued ECoG experiments."""

from __future__ import annotations

from .base import BaseClassificationParadigm


class EpochedClassification(BaseClassificationParadigm):
    """Classify cued trials (cut from dataset annotations).

    Parameters
    ----------
    events : list of str or None
        Cue names to keep (must exist in ``dataset.event_id``). None keeps
        every cue the dataset defines.
    tmin, tmax : float
        Epoch window relative to cue onset; ``tmax=None`` uses the dataset's
        default trial length.
    min_classes : int
        A dataset is valid only if at least this many requested cues exist.
    fmin, fmax, resample, channels, baseline
        See :class:`~moecog.paradigms.base.BaseParadigm`.
    """

    def __init__(self, events=None, tmin=0.0, tmax=None, fmin=1.0, fmax=200.0,
                 resample=None, channels=None, baseline=None, min_classes=2):
        super().__init__(tmin=tmin, tmax=tmax, baseline=baseline, fmin=fmin, fmax=fmax,
                         resample=resample, channels=channels)
        self.events = list(events) if events is not None else None
        self.min_classes = min_classes

    def used_events(self, dataset):
        if dataset.event_id is None:
            return {}
        if self.events is None:
            return dict(dataset.event_id)
        return {k: dataset.event_id[k] for k in self.events if k in dataset.event_id}

    def is_valid(self, dataset):
        return dataset.interval is not None and len(self.used_events(dataset)) >= self.min_classes

    #: Headline metric (decision PRSNL-67): kappa is chance-corrected and stays
    #: honest on the imbalanced (n-back) and multi-class (finger, visual) tasks.
    headline_metric = "kappa"

    def scoring(self):
        return ["kappa", "accuracy", "balanced_accuracy"]

    @property
    def datasets(self):
        from moecog.datasets import MillerLibrary

        return [MillerLibrary]

    def __repr__(self):
        return (f"{self.__class__.__name__}(events={self.events}, tmin={self.tmin}, "
                f"tmax={self.tmax}, fmin={self.fmin}, fmax={self.fmax})")


class MotorClassification(EpochedClassification):
    """Hand (fist) vs tongue movement or imagery: motor_basic, imagery_basic,
    imagery_feedback, gestures ``mot_TH`` (3 s cues)."""

    def __init__(self, events=("hand", "tongue"), tmax=3.0, **kwargs):
        super().__init__(events=events, tmax=tmax, **kwargs)


class FingerClassification(EpochedClassification):
    """Which finger was cued (5 classes): fingerflex, gestures ``fingerflex``."""

    def __init__(self, events=("thumb", "index", "middle", "ring", "little"), tmax=2.0, **kwargs):
        super().__init__(events=events, tmax=tmax, **kwargs)


class FaceHouseClassification(EpochedClassification):
    """Face vs house picture (400 ms): faces_basic, faces_noise."""

    def __init__(self, events=("face", "house"), tmin=0.0, tmax=0.4, **kwargs):
        super().__init__(events=events, tmin=tmin, tmax=tmax, **kwargs)


class VisualSearchClassification(EpochedClassification):
    """Cued arrow direction (4 classes, 2 s): visual_search."""

    def __init__(self, events=("right", "left", "down", "up"), tmax=2.0, **kwargs):
        super().__init__(events=events, tmax=tmax, **kwargs)


class NBackTargetClassification(EpochedClassification):
    """Target vs non-target picture (600 ms, imbalanced 1:4): memory_nback."""

    def __init__(self, events=("target", "nontarget"), tmax=0.6, **kwargs):
        super().__init__(events=events, tmax=tmax, **kwargs)

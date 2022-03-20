import os
import pytest
import shutil
import tempfile

from pathlib import Path

from nip import parse, dump, load, construct
from nip.utils import deep_equals

import builders

class TestConfigLoadDump:
    save_folder: Path

    @classmethod
    def setup_class(cls):
        cls.save_folder = Path(tempfile.mkdtemp())

    # def teardown_method(self):
    #     if os.path.isfile(self.save_path):
    #         os.remove(self.save_path)
    #
    # @classmethod
    # def teardown_class(cls):
    #     if os.path.isdir(cls.save_folder):
    #         shutil.rmtree(cls.save_folder)

    @pytest.mark.parametrize(
        'config_path', ['configs/config.nip', 'configs/document.nip']
    )
    def test_load_dump(self, config_path):
        config_path = Path(config_path)
        for config in parse(config_path, always_iter=True):
            obj = construct(config)
            save_path = self.save_folder.joinpath(f"{config_path.stem}.nip")
            dump(save_path, config)
            reproduced_obj = load(save_path)
            print(obj)
            print(reproduced_obj)
            assert deep_equals(reproduced_obj, obj)

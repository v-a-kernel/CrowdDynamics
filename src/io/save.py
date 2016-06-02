import datetime
import os

import h5py
import numpy as np

from src.io.attributes import Attrs


class Save(object):
    HDF5 = ".hdf5"

    def __init__(self, dirpath, name):
        # Path to root directory and filename
        self.root = dirpath
        self.name = name

        os.makedirs(self.root, exist_ok=True)

        # HDF5
        self.hdf_filepath = os.path.join(self.root, self.name + self.HDF5)
        self.group_name = None
        self.hdf_savers = None
        # New HDF5 File
        with h5py.File(self.hdf_filepath, mode='a') as file:
            # Group Name
            groups = (int(name) for name in file if name.isdigit())
            try:
                num = max(groups) + 1
            except ValueError:
                # If generator is empty
                num = 0
            self.group_name = "{:04d}".format(num)
            # Create Group
            group = file.create_group(self.group_name)
            # Metadata
            # TODO: start/end time, simulation length
            group.attrs["timestamp"] = str(datetime.datetime.now())

        # TODO: Bytes saved, memory consumption

    def new_hdf_saver(self, struct, attrs: Attrs):
        """

        :param struct: numba.jitclass
        :param attrs: attributes of the jitclass
        :return: Generator that saves records and dumps data into hdf5
        """
        struct_name = struct.__class__.__name__.lower()
        attrs.check_hasattr(struct)

        # HDF5 File
        # TODO: Attributes for new group?
        with h5py.File(self.hdf_filepath, mode='a') as file:
            base = file[self.group_name]
            # New group for struct
            group = base.create_group(struct_name)
            # Create new datasets
            for attr in attrs:
                value = np.copy(getattr(struct, attr.name))
                if attr.is_resizable:  # Resizable?
                    # Resizable
                    value = np.array(value)
                    maxshape = (None,) + value.shape
                    value = np.expand_dims(value, axis=0)
                    group.create_dataset(attr.name, data=value,
                                         maxshape=maxshape)
                else:
                    # Not Resizable
                    group.create_dataset(attr.name, data=value)

        recordable = Attrs(filter(lambda attr: attr.is_recordable, attrs),
                           attrs.save_func)
        if len(recordable) and recordable.save_func is not None:
            # TODO: Force save
            def gen():
                buffer = {attr.name: [] for attr in recordable}
                end = 1
                start = 0
                while True:
                    is_save = recordable.save_func
                    if callable(is_save):
                        is_save = is_save()
                    for attr in recordable:
                        # Append value to buffer
                        value = np.copy(getattr(struct, attr.name))
                        buffer[attr.name].append(value)
                        # Save values to hdf
                        if is_save:
                            values = np.array(buffer[attr.name])
                            with h5py.File(self.hdf_filepath, mode='a') as file:
                                dset = file[self.group_name][struct_name][attr.name]
                                new_shape = (end+1,) + values.shape[1:]
                                dset.resize(new_shape)
                                dset[start+1:] = values
                            buffer[attr.name].clear()
                    if is_save:
                        start = end
                    end += 1
                    yield
            return gen()
        else:
            return None

    def generic(self, *folders, fname=None, exists_ok=True):
        folder_path = os.path.join(self.root, *folders)
        os.makedirs(folder_path, exist_ok=True)
        if fname is None:
            fname = str(datetime.datetime.now()).replace(" ", "_")
        file_path = os.path.join(folder_path, fname)
        if not exists_ok and os.path.exists(file_path):
            raise FileExistsError("File: {}".format(file_path))
        else:
            return file_path

    def animation(self, fname=None):
        folder = "animations"
        return self.generic(folder, fname=fname, exists_ok=True)

    def figure(self, fname=None):
        folder = "figures"
        return self.generic(folder, fname=fname, exists_ok=True)

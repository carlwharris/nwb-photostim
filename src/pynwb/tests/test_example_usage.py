from datetime import datetime
from dateutil.tz import tzlocal
from pynwb import NWBFile
from pynwb.testing import TestCase
import numpy as np
from pynwb import NWBHDF5IO
from pynwb import register_class, load_namespaces
from pynwb import register_map

from pynwb.image import GrayscaleImage
# from file_classes import SpatialLightModulator, PhotostimulationDevice, HolographicPattern, PhotostimulationSeries, PhotostimulationTable
from ndx_photostim import SpatialLightModulator, PhotostimulationDevice, HolographicPattern, PhotostimulationSeries, PhotostimulationTable
import matplotlib.pyplot as plt
import os
from hdmf.build import ObjectMapper

# os.system('python file_defined_namespace.py')

def get_SLM():
    slm = SpatialLightModulator(name="slm", size=np.array([1, 2, 3]))
    return slm

def get_photostim_device():
    slm = get_SLM()
    photostim_dev = PhotostimulationDevice(name="photostim_dev", description="photostim_device", type='LED',
                                           wavelength=320, slm=slm,
                                           opsin='test_opsin', peak_pulse_energy=20,
                                           power=10, pulse_rate=5)
    return photostim_dev

def get_photostim_series():
    hp = get_holographic_pattern()

    photostim_series = PhotostimulationSeries(name="photosim series", pattern=hp, unit='SIunit',
                                              data=[1, -1, 1, -1],
                                              timestamps=[0.5, 1, 2, 4], format='interval')
    return photostim_series

def get_holographic_pattern():
    image_mask_roi = TestHolographicPattern._create_image_mask_roi()
    hp = HolographicPattern(name='pattern', image_mask_roi=image_mask_roi, roi_size=5)
    return hp

def create_NWB_file():
    nwb_file = NWBFile(session_description='test file', identifier='EXAMPLE_ID',
                       session_start_time=datetime.now(tzlocal()))
    return nwb_file


class TestSLM(TestCase):
    def test_SpatialLightModulator(self):
        slm = get_SLM()

        with self.assertRaises(ValueError):
            SpatialLightModulator(name="slm", size=np.array([[1, 2], [3, 4]]))

        nwb_file = create_NWB_file()
        nwb_file.add_device(slm)

class TestPhotostimulationDevice(TestCase):
    def test_PhotostimulationDevice(self):
        photostim_dev = PhotostimulationDevice(name="photostim_dev", description="photostim_device", type='LED',
                                               wavelength=320,
                                               opsin='test_opsin', peak_pulse_energy=20,
                                               power=10, pulse_rate=5)
        slm = get_SLM()
        photostim_dev.add_slm(slm)
        nwb_file = create_NWB_file()
        nwb_file.add_device(photostim_dev)

        with NWBHDF5IO("tmp_test.nwb", "w") as io:
            io.write(nwb_file)

        with NWBHDF5IO("tmp_test.nwb", "r", load_namespaces=True) as io:
            read_nwbfile = io.read()

        assert "photostim_dev" in read_nwbfile.devices
        read_dev = read_nwbfile.get_device('photostim_dev')
        assert read_dev.slm.name == slm.name
        assert all(read_dev.slm.size == slm.size)

        assert read_dev.name == photostim_dev.name
        assert read_dev.description == photostim_dev.description
        assert read_dev.type == photostim_dev.type
        assert read_dev.wavelength == photostim_dev.wavelength

class TestHolographicPattern(TestCase):
    def test_HolographicPatternConstructor_MaskROI(self):
        image_mask_roi = self._create_image_mask_roi()
        hp = HolographicPattern(name='hp', image_mask_roi=image_mask_roi, roi_size=5)

        HolographicPattern(name='hp', image_mask_roi=np.round(np.random.rand(5, 5)),
                           roi_size=5)
        HolographicPattern(name='hp', image_mask_roi=np.round(np.random.rand(5, 5, 5)),
                           roi_size=5)

        with self.assertRaises(ValueError):
            HolographicPattern(name='hp', image_mask_roi=np.round(np.random.rand(5)),
                               roi_size=5)

        with self.assertRaises(ValueError):
            HolographicPattern(name='hp', image_mask_roi=np.round(np.random.rand(5, 5, 5, 5)),
                               roi_size=5)

        hp = HolographicPattern(name='hp', image_mask_roi=np.round(np.random.rand(5, 5)),
                                roi_size=5)
        assert hp.dimension == (5, 5)

        # Check image_mask_roi validation
        with self.assertRaises(ValueError):
            HolographicPattern(name='hp', image_mask_roi=np.random.rand(5, 5) * 10,
                               roi_size=5)

        # with self.assertRaises(ValueError):
        #     HolographicPattern(name='hp', image_mask_roi=np.random.rand(5, 5) * -1,
        #                        ROI_size=5)

    def test_HolographicPatternConstructor_PixelROI(self):
        pixel_roi = self._create_pixel_roi()
        hp = HolographicPattern(name='hp', pixel_roi=pixel_roi, roi_size=8, dimension=[100, 100])
        hp.pixel_to_image_mask_roi()
        hp.show_mask()

        hp = HolographicPattern(name='hp', pixel_roi=pixel_roi, roi_size=[8, 4], dimension=[100, 100])
        hp.pixel_to_image_mask_roi()
        hp.show_mask()
    #
    # def test_HolographicPattern_StimulationImage(self):
    #     tiff_file = '/Users/harriscaw/Documents/NWB/220721-test-notebook-data/data/220715-i4166/pattern/920nm_00001_pattern1.tif'
    #
    #     from PIL import Image
    #     im = Image.open(tiff_file)
    #     imarray = np.array(im)
    #     im.show()
    #
    #     plt.imshow(imarray, cmap='gray', vmin=0, vmax=255)
    #     # GrayscaleImage()

    @staticmethod
    def _create_pixel_roi():
        pixel_roi = []

        for i in range(5):
            x = np.random.randint(0, 90)
            y = np.random.randint(0, 90)

            for ix in range(x, x + 1):
                for iy in range(y, y + 1):
                    pixel_roi.append((ix, iy))

        return pixel_roi

    @staticmethod
    def _create_image_mask_roi():
        image_mask_roi = np.zeros((50, 50))
        x = np.random.randint(0, 3)
        y = np.random.randint(0, 3)
        image_mask_roi[x:x + 5, y:y + 5] = 1
        return image_mask_roi

class TestPhotostimulationSeries(TestCase):
    def test_PhotostimulationSeries_Constructor(self):
        hp = get_holographic_pattern()
        series = PhotostimulationSeries(name="photosim series", format='interval', pattern=hp, data=[1, -1, 1, -1], timestamps=[0.5, 1, 2, 4], stimulus_method="stim_method", sweeping_method="method")

        nwb_file = create_NWB_file()
        nwb_file.add_stimulus(series)
        # nwb_file.add_scratch(ps)
        # assert "photosim series" in nwb_file.stimulus

        with NWBHDF5IO("basics_tutorial.nwb", "w") as io:
            io.write(nwb_file)

        with NWBHDF5IO("basics_tutorial.nwb", "r", load_namespaces=True) as io:
            read_nwbfile = io.read()
            print('')

        PhotostimulationSeries(name="photosim series", pattern=hp, format='series', data=[0, 0, 0, 1, 1, 0],
                               rate=10., stimulus_duration=0.05)

        with self.assertRaises(ValueError):
            PhotostimulationSeries(name="photosim series", pattern=hp, format='series', data=[0, 0, 0, 1, 1, 0],
                               rate=10.)

            PhotostimulationSeries(name="photosim series", pattern=hp, format='series')

        series = PhotostimulationSeries(name="photosim series", pattern=hp, format='series',
                                                  stimulus_duration = 0.05, data=[0, 0, 0, 1, 1, 0],
                                                  timestamps=[0, 0.5, 1, 1.5, 3, 6])



    def test_PhotostimulationSeriesFormatData(self):
        hp = get_holographic_pattern()
        data = [1, -1, 1, -1]
        timestamps=[0.5, 1, 2, 4]

        with self.assertRaises(ValueError):
            PhotostimulationSeries(name="photosim series", format='interval', pattern=hp, timestamps=timestamps)

        PhotostimulationSeries(name="photosim series", format='interval', pattern=hp, timestamps=timestamps, data=data)

        data = [1, -1, 1, 2]
        timestamps = [0.5, 1, 2, 4]
        with self.assertRaises(ValueError):
            PhotostimulationSeries(name="photosim series", pattern=hp, format='interval', data=data, timestamps=timestamps)

        with self.assertRaises(ValueError):
            PhotostimulationSeries(name="photosim series", pattern=hp, format='series',
                               data=[0, 0, 0, 1, 2, 0], rate=10.)

    def test_add_interval(self):
        hp = get_holographic_pattern()
        #
        empty_series = PhotostimulationSeries(name="photosim series", pattern=hp, format='interval')
        empty_series.add_interval(10, 20)
        empty_series.add_interval(30, 40)
        assert empty_series.data[0] == 1
        assert empty_series.data[3] == -1
        assert len(empty_series.data) == 4

        assert empty_series.timestamps[0] == 10
        assert empty_series.timestamps[1] == 20
        assert len(empty_series.timestamps) == 4

        stim_series_2 = PhotostimulationSeries(name="series 2", format='interval',  data=[1, -1], timestamps=[1, 3], pattern=hp)
        stim_series_2.add_interval(10., 20.)
        stim_series_2.add_interval(35., 40.)

        # import os
        # os.remove("basics_tutorial.h5")
        # with NWBHDF5IO("basics_tutorial.h5", "w") as io:
        #     io.write(stim_series_2)
        #
        # with NWBHDF5IO("basics_tutorial.h5", "r", load_namespaces=True) as io:
        #     read_nwbfile = io.read()
        # print(read_nwbfile)

    def test_add_onset(self):
        hp = get_holographic_pattern()

        ps = PhotostimulationSeries(name="photosim series",  format='series', pattern=hp, stimulus_duration=10)
        ps.add_onset(10)
        ps.add_onset([30, 40, 50])

        assert all(ps.timestamps == np.array([10., 30., 40., 50.]))
        assert all(ps.data == np.array([1., 1., 1., 1.]))

        ps = PhotostimulationSeries(name="photosim series", format='interval', pattern=hp, stimulus_duration=2)
        ps.add_onset(10)
        ps.add_onset([30, 40, 50])

        assert all(ps.timestamps == np.array([10., 12., 30., 32., 40., 42., 50., 52.]))
        assert all(ps.data == np.array([ 1., -1.,  1., -1.,  1., -1.,  1., -1.]))


    def test_to_df(self):
        hp = get_holographic_pattern()

        ps = PhotostimulationSeries(name="photosim series", format='series', pattern=hp,
                               data=[0, 0, 0, 1, 1, 0], rate=10., stimulus_duration=4)
        ps.to_dataframe()

        ps = PhotostimulationSeries(name="photosim series",format='series', pattern=hp,
                                    stimulus_duration=0.05, data=[0, 0, 0, 1, 1, 0], timestamps=[0, 0.5, 1, 1.5, 3, 6])
        ps.to_dataframe()

        ps = PhotostimulationSeries(name="photosim series",format='interval', pattern=hp,  stimulus_duration=2)
        ps.add_onset([10, 40, 50])
        ps.to_dataframe()

    def test_PhotostimulationSeries_StartStopList(self):
        hp = get_holographic_pattern()
        ps = PhotostimulationSeries(name="photosim series", format='interval', pattern=hp, data=[1, -1, 1, -1],
                               timestamps=[0.5, 1, 2, 4])

        lst = ps._get_start_stop_list()

        ps = PhotostimulationSeries(name="photosim series", pattern=hp, format='series',
                               data=[0, 0, 0, 1, 1, 0], rate=10., stimulus_duration=4)
        lst = ps._get_start_stop_list()

        ps = PhotostimulationSeries(name="photosim series", pattern=hp,
                                                  format='series', stimulus_duration=0.05,
                                                  data=[0, 0, 0, 1, 1, 0], timestamps=[0, 0.5, 1, 1.5, 3, 6])
        lst = ps._get_start_stop_list()
        print('')



class TestPhotostimulationTable(TestCase):
    def test_PhotostimulationTableConstructor(self):
        dev = get_photostim_device()
        hp = get_holographic_pattern()


        nwbfile = NWBFile('my first synthetic recording', 'EXAMPLE_ID', datetime.now(tzlocal()), )
        nwbfile.add_device(dev)

        sp = PhotostimulationTable(name='test', description='test desc', device=dev)
        s1 = PhotostimulationSeries(name="series1", pattern=hp, format='interval',
                                    stimulus_duration=2, data=[1, -1, 1, -1], timestamps=[0.5, 1, 2, 4])
        s2 = PhotostimulationSeries(name="series2", pattern=hp, format='interval',
                                    stimulus_duration=2, data=[1, -1, 1, -1], timestamps=[0.5, 1, 2, 4])
        s3 = PhotostimulationSeries(name="series3", pattern=hp, format='interval',
                                    stimulus_duration=2, data=[1, -1, 1, -1], timestamps=[0.5, 1, 2, 4])

        [nwbfile.add_stimulus(s) for s in [s1, s2, s3]]
        sp.add_series([s1, s2, s3])#, row_name=["row_1", "row_2", "row_3"])

        behavior_module = nwbfile.create_processing_module(
            name="holographic_photostim", description="initial data"
        )
        behavior_module.add(sp)
        with NWBHDF5IO("basics_tutorial.nwb", "w") as io:
            io.write(nwbfile)

        with NWBHDF5IO("basics_tutorial.nwb", "r", load_namespaces=True) as io:
            read_nwbfile = io.read()


    def test_PhotostimulationTable(self):
        hp = get_holographic_pattern()
        series = get_photostim_series()
        dev = get_photostim_device()

        nwbfile = NWBFile('my first synthetic recording','EXAMPLE_ID', datetime.now(tzlocal()),)

        nwbfile.add_device(dev)
        sp = PhotostimulationTable(name='test', description='test desc', device=dev)
        s1 = PhotostimulationSeries(name="series1", pattern=hp, format='interval',
                                    stimulus_duration=2, data=[1, -1, 1, -1], timestamps=[0.5, 1, 2, 4])
        s2 = PhotostimulationSeries(name="series2", pattern=hp, format='interval',
                                    stimulus_duration=2, data=[1, -1, 1, -1], timestamps=[0.5, 1, 2, 4])
        s3 = PhotostimulationSeries(name="series3", pattern=hp, format='interval',
                                    stimulus_duration=2, data=[1, -1, 1, -1], timestamps=[0.5, 1, 2, 4])

        [nwbfile.add_stimulus(s) for s in [s1, s2, s3]]
        sp.add_series([s1, s2, s3])
        df = sp.to_dataframe()
        print(df)
        behavior_module = nwbfile.create_processing_module(
            name="holographic_photostim", description="initial data"
        )
        behavior_module.add(sp)
        with NWBHDF5IO("basics_tutorial.nwb", "w") as io:
            io.write(nwbfile)

        with NWBHDF5IO("basics_tutorial.nwb", "r", load_namespaces=True) as io:
            read_nwbfile = io.read()

    def test_PhotostimulationTable_plot(self):
        hp = get_holographic_pattern()
        dev = get_photostim_device()

        nwbfile = NWBFile('my first synthetic recording', 'EXAMPLE_ID', datetime.now(tzlocal()), )

        nwbfile.add_device(dev)
        sp = PhotostimulationTable(name='test', description='test desc', device=dev)
        s1 = PhotostimulationSeries(name="series1", pattern=hp, format='interval',
                                    stimulus_duration=2, data=[1, -1, 1, -1], timestamps=[0.5, 1, 2, 4])
        s2 = PhotostimulationSeries(name="series2", pattern=hp, format='interval',
                                    stimulus_duration=2, data=[1, -1, 1, -1], timestamps=[0.5, 1, 2, 4])
        s3 = PhotostimulationSeries(name="series3", pattern=hp, format='interval',
                                    stimulus_duration=2, data=[1, -1, 1, -1], timestamps=[0.5, 1, 2, 4])

        [nwbfile.add_stimulus(s) for s in [s1, s2, s3]]
        sp.add_series([s1, s2, s3])

        sp.plot_presentation_times()

if os.path.exists("tmp_test.nwb"):
    os.remove("tmp_test.nwb")
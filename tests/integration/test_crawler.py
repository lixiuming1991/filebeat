from filebeat import TestCase

import os
import time

# Additional tests to be added:
# * Check what happens when file renamed -> no recrawling should happen
# * Check if file descriptor is "closed" when file disappears
class Test(TestCase):
    def test_fetched_lines(self):
        # Checks if all lines are read from the log file

        self.render_config_template(
            path=os.path.abspath(self.working_dir) + "/log/*"
        )
        os.mkdir(self.working_dir + "/log/")

        testfile =  self.working_dir + "/log/test.log"
        file = open(testfile, 'w')

        iterations = 80
        for n in range(0, iterations):
            file.write("hello world" + str(n))
            file.write("\n")


        file.close()

        filebeat = self.start_filebeat()

        # TODO: Find better solution when filebeat did crawl the file
        # Idea: Special flag to filebeat so that filebeat is only doing and crawl and then finishes
        time.sleep(10)
        filebeat.kill_and_wait()

        i = 0

        # Count lines of filebeat generated file
        with open(self.working_dir + "/output/filebeat") as f:
            for i, l in enumerate(f, 1):
                pass

        # Check that output file has the same number of lines as the log file
        assert iterations == i


    def test_unfinished_line(self):
        # Checks that if a line does not have a line ending, is is not read yet

        self.render_config_template(
            path=os.path.abspath(self.working_dir) + "/log/*"
        )
        os.mkdir(self.working_dir + "/log/")

        testfile =  self.working_dir + "/log/test.log"
        file = open(testfile, 'w')

        iterations = 80
        for n in range(0, iterations):
            file.write("hello world" + str(n))
            file.write("\n")

        # An additional line is written to the log file. This line should not be read
        # as there is no finishing \n or \r
        file.write("unfinished line")

        file.close()

        filebeat = self.start_filebeat()

        # TODO: Find better solution when filebeat did crawl the file
        time.sleep(10)
        filebeat.kill_and_wait()

        i = 0

        # Count lines of filebeat generated file
        with open(self.working_dir + "/output/filebeat") as f:
            for i, l in enumerate(f, 1):
                pass

        # Check that output file has the same number of lines as the log file
        assert iterations == i


    def test_file_renaming(self):
        # Makes sure that when a file is renamed, the content is not read again.

        self.render_config_template(
            path=os.path.abspath(self.working_dir) + "/log/*"
        )
        os.mkdir(self.working_dir + "/log/")

        testfile1 =  self.working_dir + "/log/test-old.log"
        file = open(testfile1, 'w')

        iterations = 5
        for n in range(0, iterations):
            file.write("old file")
            file.write("\n")

        file.close()

        filebeat = self.start_filebeat()

        # Let it read the file
        time.sleep(5)

        # Rename the file (no new file created)
        testfile2 = self.working_dir + "/log/test-new.log"
        os.rename(testfile1, testfile2)
        file = open(testfile2, 'a')

        iterations = 5
        for n in range(0, iterations):
            file.write("new file")
            file.write("\n")

        file.close()


        # let it read the new file
        time.sleep(20)

        filebeat.kill_and_wait()

        i = 0

        # Count lines of filebeat generated file
        with open(self.working_dir + "/output/filebeat") as f:
            for i, l in enumerate(f, 1):
                pass

        # Make sure all 10 lines were read
        assert i == 10

    def test_file_disappear(self):
        # Checks that filebeat keeps running in case a log files is deleted

        self.render_config_template(
            path=os.path.abspath(self.working_dir) + "/log/*"
        )
        os.mkdir(self.working_dir + "/log/")

        testfile =  self.working_dir + "/log/test.log"
        file = open(testfile, 'w')

        iterations = 5
        for n in range(0, iterations):
            file.write("disappearing file")
            file.write("\n")

        file.close()

        filebeat = self.start_filebeat()

        # Let it read the file
        time.sleep(5)
        os.remove(testfile)
        time.sleep(5)

        # Create new file to check if new file is picked up
        testfile2 =  self.working_dir + "/log/test2.log"
        file = open(testfile2, 'w')

        iterations = 5
        for n in range(0, iterations):
            file.write("new file")
            file.write("\n")

        file.close()

        time.sleep(5)

        filebeat.kill_and_wait()

        data = self.get_dot_filebeat()

        # Make sure new file was picked up, old file should stay in
        assert len(data) == 2

        # Make sure output has 10 entries
        output = self.get_filebeat_output()

        assert len(output) == 2 * 5


    def test_file_disappear_appear(self):
        # Checks that filebeat keeps running in case a log files is deleted

        self.render_config_template(
            path=os.path.abspath(self.working_dir) + "/log/*"
        )
        os.mkdir(self.working_dir + "/log/")

        testfile =  self.working_dir + "/log/test.log"
        file = open(testfile, 'w')

        iterations = 5
        for n in range(0, iterations):
            file.write("disappearing file")
            file.write("\n")

        file.close()

        filebeat = self.start_filebeat()

        # Let it read the file
        time.sleep(5)
        os.remove(testfile)
        time.sleep(5)

        # Create new file with same to see if it is picked up
        file = open(testfile, 'w')

        iterations = 5
        for n in range(0, iterations):
            file.write("new file")
            file.write("\n")

        file.close()

        time.sleep(5)

        filebeat.kill_and_wait()

        data = self.get_dot_filebeat()

        # Make sure new file was picked up. As it has the same file name, only one entry exists
        assert len(data) == 1

        # Make sure output has 10 entries, the new file was started from scratch
        output = self.get_filebeat_output()
        assert len(output) == 2 * 5


class VMManager:
    def __init__(self):
        self.PM = [0] * 524288  # Physical memory array
        self.DISK = [[0] * 512 for _ in range(1024)]  # Disk array
        self.segment_table = {}  # Dictionary to store segment table entries
        self.page_tables = {}    # Dictionary to store page tables
        self.used_frames = {0, 1}  # Frames 0,1 reserved for ST (2 frames since each entry is 2 integers)
        self.next_free_frame = 2  # Will be updated after initialization
        self.highest_frame = 1    # Track highest frame number seen

    def get_next_free_frame(self):
        """Find the next available free frame."""
        frame = max(self.next_free_frame, self.highest_frame + 1)
        while frame in self.used_frames:
            frame += 1
        self.used_frames.add(frame)
        self.next_free_frame = frame + 1
        return frame

    def initialize_from_file(self, init_file):
        """Initialize segment and page tables from input file."""
        try:
            with open(init_file, 'r') as file:
                # Read segment table entries (Line 1: s1 z1 f1 s2 z2 f2 ... sn zn fn)
                segment_line = file.readline().strip().split()
                for i in range(0, len(segment_line), 3):
                    s = int(segment_line[i])      # segment number
                    z = int(segment_line[i + 1])  # segment size
                    frame = int(segment_line[i + 2])  # frame/block number
                    
                    # Set segment size in ST: PM[2s] = z
                    self.PM[2 * s] = z
                    # Set PT location in ST: PM[2s+1] = frame
                    self.PM[2 * s + 1] = frame
                    
                    if frame > 0:  # PT is in memory
                        self.used_frames.add(frame)
                        self.highest_frame = max(self.highest_frame, frame)

                # Read page table entries (Line 2: s1 p1 f1 s2 p2 f2 ... sm pm fm)
                page_line = file.readline().strip().split()
                for i in range(0, len(page_line), 3):
                    s = int(page_line[i])      # segment number
                    p = int(page_line[i + 1])  # page number
                    frame = int(page_line[i + 2])  # frame/block number
                    
                    if self.PM[2 * s + 1] > 0:  # If PT is resident
                        # Set page frame in PT: PM[PT_base + p] = frame
                        pt_base = self.PM[2 * s + 1] * 512
                        self.PM[pt_base + p] = frame
                        if frame > 0:  # Page is in memory
                            self.used_frames.add(frame)
                            self.highest_frame = max(self.highest_frame, frame)
                    else:  # PT is on disk
                        # Store in disk: D[|PT_block|][p] = frame
                        disk_block = abs(self.PM[2 * s + 1])
                        self.DISK[disk_block][p] = frame
                        if frame > 0:  # Track highest frame even if on disk
                            self.highest_frame = max(self.highest_frame, frame)

                # Update next_free_frame to be after highest frame seen
                self.next_free_frame = self.highest_frame + 1

        except Exception as e:
            print(f"Error initializing from file: {e}")
            raise

    def translate_address(self, va):
        """Translate virtual address to physical address."""
        # Extract s, p, w from VA (each 9 bits)
        w = va & 0x1FF          # Last 9 bits
        p = (va >> 9) & 0x1FF   # Middle 9 bits
        s = (va >> 18) & 0x1FF  # First 9 bits
        pw = va & 0x3FFFF       # Last 18 bits (p and w combined)

        # Check if segment exists and if VA is within segment bounds
        if s * 2 >= len(self.PM) or self.PM[2 * s] == 0:
            return None  # Segment fault
        if pw >= self.PM[2 * s]:
            return None  # Offset beyond segment size

        # Get PT location from ST
        pt_loc = self.PM[2 * s + 1]
        
        # If PT is not resident (negative frame number)
        if pt_loc < 0:
            # Handle PT page fault
            new_frame = self.get_next_free_frame()
            disk_block = abs(pt_loc)
            # Copy PT from disk to memory
            for i in range(512):
                self.PM[new_frame * 512 + i] = self.DISK[disk_block][i]
            # Update ST entry
            self.PM[2 * s + 1] = new_frame
            pt_loc = new_frame

        # Get page frame from PT
        page_frame = self.PM[pt_loc * 512 + p]
        
        # If page is not resident (negative frame number)
        if page_frame < 0:
            # Handle page fault
            new_frame = self.get_next_free_frame()
            disk_block = abs(page_frame)
            # In real implementation, would copy page from disk
            # Update PT entry
            self.PM[pt_loc * 512 + p] = new_frame
            page_frame = new_frame

        # Calculate final physical address
        return page_frame * 512 + w

    def process_addresses(self, input_file, output_file):
        """Process virtual addresses from input file and write results to output file."""
        with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
            vas = fin.readline().strip().split()
            results = []
            for va in vas:
                pa = self.translate_address(int(va))
                if pa is not None:
                    results.append(str(pa))
                else:
                    results.append("-1")
            fout.write(" ".join(results))

def main():
    vm = VMManager()
    vm.initialize_from_file("init-dp.txt")
    vm.process_addresses("input-dp.txt", "output.txt")

if __name__ == "__main__":
    main()

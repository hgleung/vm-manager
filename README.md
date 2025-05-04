# Virtual Memory Manager for UC Irvine CS 143B

This project implements a virtual memory manager that simulates the translation of virtual addresses to physical addresses using a two-level paging system. The implementation follows the requirements for the UC Irvine CS 143B course project.

## How to Run

Run the following command in the terminal with the initialization file named `init-dp.txt` and input file named `input-dp.txt`:

```
python3 virtual_memory.py
```

## Implementation Overview

The core of the project is implemented in `virtual_memory.py`, which defines a `VMManager` class responsible for managing the segment table, page tables, physical memory, and disk simulation. The program reads initialization and address input files, processes virtual address translations, and writes the results to `output.txt`.

### Data Structures
- **Physical Memory (PM):** Simulated as a large array (`self.PM`) of 524,288 integers, representing 1024 frames of 512 words each.
- **Disk (DISK):** Simulated as a 2D array (`self.DISK`) with 1024 blocks, each containing 512 words, used to hold non-resident page tables and pages.
- **Segment Table:** Stored in the first part of `PM`. Each segment has two entries: segment size and the frame/block number of its page table (positive for resident in memory, negative for on disk).
- **Page Tables:** Each page table is allocated to a frame in `PM` or a block in `DISK`.
- **Used Frames:** A set to track which frames are currently allocated to avoid collisions.

### Initialization (`initialize_from_file`)
- Reads segment table and page table entries from `init-dp.txt`.
- Segment table entries specify segment number, size, and page table location.
- Page table entries specify segment, page, and frame/block for each page.
- Populates `PM` and `DISK` accordingly, marking frames as used and updating the highest frame number seen.

### Address Translation (`translate_address`)
- Virtual addresses are 27 bits, split into segment (s), page (p), and offset (w), each 9 bits.
- Checks if the segment exists and if the address is within bounds.
- Retrieves the page table location; if not resident, simulates a page table fault by loading it from disk into the next free frame.
- Retrieves the page frame; if not resident, simulates a page fault by loading it from disk (logic placeholder).
- Computes the final physical address as `frame * 512 + offset`.
- Returns `-1` for segment faults or out-of-bounds accesses.

### Processing Input Addresses (`process_addresses`)
- Reads a list of virtual addresses from `input-dp.txt`.
- Translates each address using `translate_address`.
- Writes the resulting physical addresses (or `-1` for faults) to `output.txt`.

### Main Function
- Creates a `VMManager` instance, initializes it from `init-dp.txt`, and processes addresses from `input-dp.txt`.

## Example Files
- `init-dp.txt`: Contains segment and page table initialization data.
- `input-dp.txt`: Contains virtual addresses to be translated.
- `output.txt`: Output file with resulting physical addresses.

## Error Handling
- The implementation prints errors encountered during initialization and raises exceptions for critical failures.
- Segment faults and out-of-bounds accesses are handled by returning `-1` as specified.

## Notes
- The simulation assumes that the disk contains valid data for non-resident page tables and pages.
- The logic for loading a page from disk is a placeholder, as the project focuses on address translation and page fault handling.


---
This emulator is designed for educational use in UC Irvine's CS 143B course to illustrate file system principles and provide hands-on experience with file system operations.

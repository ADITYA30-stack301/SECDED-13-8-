
`timescale 1ns/1ps

module crc8_vector_tb;

    reg  [7:0] crc_in, data;
    wire [7:0] crc_out;

    reg [71:0] mem [0:999];
    reg [7:0] crc_temp;

    integer n, i;
    integer mismatches;

    // CRC module instantiation
    crc_8 uut (
        .crc_in  (crc_in),
        .data    (data),
        .crc_out (crc_out)
    );

    initial begin

        // Load test vectors
        $readmemh("crc_frames.mem", mem);

        mismatches = 0;

        // Process all 1000 frames
        for (n = 0; n < 1000; n = n + 1) begin

            crc_in = 8'h00;

            // Process 8 payload bytes
            for (i = 0; i < 8; i = i + 1) begin

                data = mem[n][71 - (i * 8) -: 8];

                #1;

                crc_temp = crc_out;
                crc_in = crc_temp;

            end

           
            if (crc_temp !== mem[n][7:0]) begin

                mismatches = mismatches + 1;

                // Print only first 10 mismatches
                if (mismatches <= 10) begin
                    $display("MISMATCH Frame=%0d Expected=%h Got=%h",
                             n, mem[n][7:0], crc_temp);
                end

            end

        end

        $display("--------------------------------");
        $display("Frames checked: 1000");
        $display("Mismatches: %0d", mismatches);
        $display("--------------------------------");

        $finish;

    end

endmodule

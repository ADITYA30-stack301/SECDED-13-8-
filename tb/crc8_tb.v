
`timescale 1ns/1ps

module crc8_tb;

    reg  [7:0] crc_in, data;
    wire [7:0] crc_out;

    // Instantiate CRC-8 module
    crc_8 uut (
        .crc_in  (crc_in),
        .data    (data),
        .crc_out (crc_out)
    );

    initial begin

        // Test 1
        crc_in = 8'h00;
        data   = 8'h01;
        #1;
        $display("crc_in=%h data=%h crc_out=%h expected=07",
                  crc_in, data, crc_out);

        // Test 2
        crc_in = 8'h00;
        data   = 8'h80;
        #1;
        $display("crc_in=%h data=%h crc_out=%h expected=89",
                  crc_in, data, crc_out);

        // Test 3
        crc_in = 8'h00;
        data   = 8'hFF;
        #1;
        $display("crc_in=%h data=%h crc_out=%h expected=f3",
                  crc_in, data, crc_out);

        // Test 4
        crc_in = 8'h07;
        data   = 8'h01;
        #1;
        $display("crc_in=%h data=%h crc_out=%h expected=12",
                  crc_in, data, crc_out);

        // Test 5
        crc_in = 8'hAB;
        data   = 8'hCD;
        #1;
        $display("crc_in=%h data=%h crc_out=%h expected=35",
                  crc_in, data, crc_out);

        $finish;
    end

endmodule

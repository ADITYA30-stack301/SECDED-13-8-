`timescale 1ns/1ps

module secded_codec_tb;

    reg  [7:0]  data;
    reg  [12:0] err;            // error pattern: 1 = flip that bit
    wire [12:0] code;           // encoder output
    wire [12:0] code_rx;        // codeword after error injection
    wire [7:0]  data_out;
    wire        corrected;
    wire        uncorrectable;

    // group masks (independent copy, used for the encoder check)
    localparam [12:0] M1 = 13'b0010101010101;
    localparam [12:0] M2 = 13'b0011001100110;
    localparam [12:0] M4 = 13'b0100001111000;
    localparam [12:0] M8 = 13'b0111110000000;

    integer i, j, k;
    integer fail_enc, fail_clean, fail_single, fail_double;

    secded_enc enc (
        .data(data),
        .code(code)
    );

    assign code_rx = code ^ err;

    secded_dec dec (
        .code_in(code_rx),
        .data_out(data_out),
        .corrected(corrected),
        .uncorrectable(uncorrectable)
    );

    initial begin
        fail_enc = 0; fail_clean = 0; fail_single = 0; fail_double = 0;
        err = 13'b0;

        // Test 0: encoder output must satisfy even parity in every group
        for (i = 0; i < 256; i = i + 1) begin
            data = i; err = 13'b0; #1;
            if ((^(code & M1)) || (^(code & M2)) ||
                (^(code & M4)) || (^(code & M8)) || (^code)) begin
                fail_enc = fail_enc + 1;
                $display("ENC FAIL: data=%b code=%b", data, code);
            end
        end

        // Test 1: no errors
        for (i = 0; i < 256; i = i + 1) begin
            data = i; err = 13'b0; #1;
            if (!(data_out === data && corrected === 1'b0 && uncorrectable === 1'b0)) begin
                fail_clean = fail_clean + 1;
                $display("CLEAN FAIL: data=%b out=%b c=%b u=%b",
                         data, data_out, corrected, uncorrectable);
            end
        end

        // Test 2: every single-bit error
        for (i = 0; i < 256; i = i + 1) begin
            for (j = 0; j < 13; j = j + 1) begin
                data = i; err = 13'b1 << j; #1;
                if (!(data_out === data && corrected === 1'b1 && uncorrectable === 1'b0)) begin
                    fail_single = fail_single + 1;
                    $display("SINGLE FAIL: data=%b flip=%0d out=%b c=%b u=%b",
                             data, j, data_out, corrected, uncorrectable);
                end
            end
        end

        // Test 3: every double-bit error
        for (i = 0; i < 256; i = i + 1) begin
            for (j = 0; j < 13; j = j + 1) begin
                for (k = j + 1; k < 13; k = k + 1) begin
                    data = i; err = (13'b1 << j) | (13'b1 << k); #1;
                    if (!(corrected === 1'b0 && uncorrectable === 1'b1)) begin
                        fail_double = fail_double + 1;
                        $display("DOUBLE FAIL: data=%b flips=%0d,%0d c=%b u=%b",
                                 data, j, k, corrected, uncorrectable);
                    end
                end
            end
        end

        $display("==========================================");
        $display("Encoder parity check : %0d failures / 256",    fail_enc);
        $display("No-error test        : %0d failures / 256",    fail_clean);
        $display("Single-error test    : %0d failures / 3328",   fail_single);
        $display("Double-error test    : %0d failures / 19968",  fail_double);
        if (fail_enc + fail_clean + fail_single + fail_double == 0)
            $display("ALL TESTS PASSED");
        else
            $display("VERIFICATION FAILED");
        $display("==========================================");
        $finish;
    end

endmodule
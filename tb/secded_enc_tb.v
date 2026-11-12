

`timescale 1ns/1ps

module secded_enc_tb;

    reg  [7:0] data;
    wire [12:0] code;

    integer i;
    integer passed;
    integer failed;

    reg [12:0] expected;

    // Device Under Test
    secded_enc uut (
        .data(data),
        .code(code)
    );

    initial begin

        passed = 0;
        failed = 0;

        $dumpfile("secded_enc.vcd");
        $dumpvars(0, secded_enc_tb);

        $display("========================================");
        $display("   SECDED ENCODER EXHAUSTIVE TEST");
        $display("========================================");

        for (i = 0; i < 256; i = i + 1) begin

            data = i;
            #10;

            // Expected encoded output
            expected[2]  = data[0];
            expected[4]  = data[1];
            expected[5]  = data[2];
            expected[6]  = data[3];
            expected[8]  = data[4];
            expected[9]  = data[5];
            expected[10] = data[6];
            expected[11] = data[7];

            // Hamming parity bits
            expected[0] = data[0]^data[1]^data[3]^data[4]^data[6];
            expected[1] = data[0]^data[2]^data[3]^data[5]^data[6];
            expected[3] = data[1]^data[2]^data[3]^data[7];
            expected[7] = data[4]^data[5]^data[6]^data[7];

            // Overall parity
            expected[12] = ^expected[11:0];

            // Compare actual and expected
            if (code === expected) begin
                passed = passed + 1;
            end
            else begin
                failed = failed + 1;

                $display("FAIL: Data=%b Expected=%b Actual=%b",
                          data, expected, code);
            end

        end

        $display("----------------------------------------");
        $display("Total test cases : 256");
        $display("Passed           : %0d", passed);
        $display("Failed           : %0d", failed);
        $display("----------------------------------------");

        if (failed == 0)
            $display("ALL TESTS PASSED!");
        else
            $display("VERIFICATION FAILED!");

        $display("========================================");

        $finish;

    end

endmodule

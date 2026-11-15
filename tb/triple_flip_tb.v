`timescale 1ns/1ps

module secded_triple_tb;

    reg  [7:0]  data;
    reg  [12:0] err;
    wire [12:0] code;
    wire [12:0] code_rx;
    wire [7:0]  data_out;
    wire        corrected;
    wire        uncorrectable;

    integer i, j, k, m;
    integer detected, lucky, silent;

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
        detected = 0;
        lucky    = 0;
        silent   = 0;
        err      = 13'b0;

        for (i = 0; i < 256; i = i + 1) begin
            for (j = 0; j < 13; j = j + 1) begin
                for (k = j + 1; k < 13; k = k + 1) begin
                    for (m = k + 1; m < 13; m = m + 1) begin
                        data = i;
                        err  = (13'b1 << j) | (13'b1 << k) | (13'b1 << m);
                        #1;

                        if (uncorrectable === 1'b1)
                            detected = detected + 1;
                        else if (data_out === data)
                            lucky = lucky + 1;
                        else
                            silent = silent + 1;
                    end
                end
            end
        end

        $display("==========================================");
        $display("Triple-bit errors (all 13 bits, all 256 data values)");
        $display("Detected (uncorrectable = 1)      : %0d", detected);
        $display("Lucky (no flag, data still right) : %0d", lucky);
        $display("Silent corruption (no flag, wrong): %0d", silent);
        $display("Sum                               : %0d (expect 73216)",
                 detected + lucky + silent);
        $display("==========================================");
        $finish;
    end

endmodule
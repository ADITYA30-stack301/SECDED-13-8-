module abc;
reg a;
initial 

begin
    $dumpfile("sim/hello.vcd");
$dumpvars(0, abc);
    $display("hello");
    a=0;
    #10 a=1;
    #15 a=0;
    #20 a=1;
    #10 $finish;

end
endmodule
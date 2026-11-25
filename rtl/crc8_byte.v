module crc_8(input[7:0] crc_in,output reg[7:0] crc_out,input[7:0]data);
integer i;
reg[7:0] c;
always @(*) begin
c = crc_in ^ data;
for(i = 0;i<8;i = i+1)begin
  if(c[7] == 1)
   c = (c << 1) ^ 8'h07;
  else
   c = c<<1;
end
crc_out = c;
end
endmodule
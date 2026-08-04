clc 
clear
close all

%% DATASET 1
% input U of 5 V at 300 Hz
data1 = csvread('data/h50us.csv'); % 200,001 samples
% 10 seconds at 20 kHz
t1 = data1(:,2); % time vector
y1 = data1(:,3)-mean(data1(:,3)); % output in micrometers
u1 = data1(:,4)-mean(data1(:,4)); % input in volts
% remove drift in measurements

figure(1)
yyaxis left
plot(t1,u1)
ylabel('Input [Volts]')
yyaxis right
plot(t1,y1)
xlim([5 5.01])
ylabel('Output [micrometers]')
xlabel('Time')
grid on
title('Case (a)')

figure(2)
plot(u1,y1,'k')
xlabel('Input [Volts]'), ylabel('Output [micrometers]')
grid on
title('Case (a)')


%% DATASET 2 
% input U of 150V at 1Hz
data2 = csvread('data/hysteresis_v_150_1hz.csv'); % 50,001 data
% 10 seconds at 5 kHz

data2 = data2(data2(:,2) > 5,:); % discard unused measurement

t2 = data2(:,2); % time vector
y2 = data2(:,3); % output in micrometers
u2 = data2(:,4); % input in volts

figure(3)
yyaxis left
plot(t2,u2)
ylabel('Input [Volts]')
yyaxis right
plot(t2,y2)
% xlim([7 9])
ylabel('Output [micrometers]')
xlabel('Time')
grid on
title('Case (b)')

figure(4)
plot(u2,y2,'k')
xlabel('Input [Volts]'), ylabel('Output [micrometers]')
grid on
title('Case (b)')



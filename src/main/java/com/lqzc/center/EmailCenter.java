//package com.lqzc.center;
//
//import jakarta.annotation.Resource;
//import org.springframework.beans.factory.annotation.Value;
//import org.springframework.mail.SimpleMailMessage;
//import org.springframework.mail.javamail.JavaMailSender;
//import org.springframework.stereotype.Service;
//
//@Service
//public class EmailCenter {
//
//    @Resource
//    private JavaMailSender mailSender;
//
//    @Value("${spring.mail.username}")
//    private String from;
//
//    public void sendEmail(String to, String subject, String content) {
//        SimpleMailMessage message = new SimpleMailMessage();
//        message.setFrom(from);
//        message.setTo(to);
//
//        message.setSubject(subject);
//        message.setText(content);
//        mailSender.send(message);
//    }
//}

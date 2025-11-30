// 日期工具函数

/**
 * 安全的日期解析，兼容iOS设备
 * @param {string|number|Date} dateInput - 日期字符串、时间戳或Date对象
 * @returns {Date} Date对象
 */
function parseDate(dateInput) {
  if (!dateInput) {
    return new Date();
  }
  
  // 如果已经是Date对象，直接返回
  if (dateInput instanceof Date) {
    return dateInput;
  }
  
  // 如果是数字（时间戳），直接转换
  if (typeof dateInput === 'number') {
    return new Date(dateInput);
  }
  
  // 如果是字符串，进行iOS兼容性处理
  if (typeof dateInput === 'string') {
    // 将 "2025-06-23 21:55:08" 格式转换为 "2025/06/23 21:55:08"
    // 这样可以兼容iOS设备
    let iosCompatibleDate = dateInput;
    
    // 匹配 yyyy-MM-dd HH:mm:ss 格式
    if (/^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$/.test(dateInput)) {
      iosCompatibleDate = dateInput.replace(/-/g, '/');
    }
    // 匹配 yyyy-MM-dd 格式
    else if (/^\d{4}-\d{2}-\d{2}$/.test(dateInput)) {
      iosCompatibleDate = dateInput.replace(/-/g, '/');
    }
    
    return new Date(iosCompatibleDate);
  }
  
  // 其他情况，尝试直接转换
  return new Date(dateInput);
}

/**
 * 格式化时间为 MM-DD HH:MM
 * @param {string|number|Date} dateInput - 日期输入
 * @returns {string} 格式化后的时间字符串
 */
function formatTime(dateInput) {
  const date = parseDate(dateInput);
  
  if (isNaN(date.getTime())) {
    return '--';
  }
  
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const hour = date.getHours();
  const minute = date.getMinutes();
  
  return [
    month.toString().padStart(2, '0'),
    day.toString().padStart(2, '0')
  ].join('-') + ' ' + [
    hour.toString().padStart(2, '0'),
    minute.toString().padStart(2, '0')
  ].join(':');
}

/**
 * 格式化日期为 YYYY-MM-DD
 * @param {string|number|Date} dateInput - 日期输入
 * @returns {string} 格式化后的日期字符串
 */
function formatDate(dateInput) {
  const date = parseDate(dateInput);
  
  if (isNaN(date.getTime())) {
    return '--';
  }
  
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  
  return [
    year,
    month.toString().padStart(2, '0'),
    day.toString().padStart(2, '0')
  ].join('-');
}

/**
 * 格式化完整日期时间为 YYYY-MM-DD HH:MM:SS
 * @param {string|number|Date} dateInput - 日期输入
 * @returns {string} 格式化后的日期时间字符串
 */
function formatDateTime(dateInput) {
  const date = parseDate(dateInput);
  
  if (isNaN(date.getTime())) {
    return '--';
  }
  
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const hour = date.getHours();
  const minute = date.getMinutes();
  const second = date.getSeconds();
  
  return [
    year,
    month.toString().padStart(2, '0'),
    day.toString().padStart(2, '0')
  ].join('-') + ' ' + [
    hour.toString().padStart(2, '0'),
    minute.toString().padStart(2, '0'),
    second.toString().padStart(2, '0')
  ].join(':');
}

module.exports = {
  parseDate,
  formatTime,
  formatDate,
  formatDateTime
}; 
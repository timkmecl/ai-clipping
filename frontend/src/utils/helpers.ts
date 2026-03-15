export const aggregators = [
  "najdi.si", "1zavse.si", "novice24.net", "novice24.si", "times.si", 
  "telex.si", "klip.si", "megasvet.si", "si21.com", "portal24.si", 
  "telegraf.si", "informer.si", "info360.si", "info0"
];

export const isAggregator = (medij: string) => {
  return aggregators.some(agg => medij.toLowerCase().includes(agg.toLowerCase()));
};

export const formatDate = (date: Date) => {
  const day = date.getDate().toString().padStart(2, '0');
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  return `${day}. ${month}.`;
};

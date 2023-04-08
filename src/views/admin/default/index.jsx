import {
  Avatar,
  Box,
  Flex,
  FormLabel,
  Icon,
  Select,
  SimpleGrid,
  useColorModeValue,
  Text, Button
} from "@chakra-ui/react";
// Assets
import Usa from "assets/img/dashboards/usa.png";
// Custom components
import MiniCalendar from "components/calendar/MiniCalendar";
import MiniStatistics from "components/card/MiniStatistics";
import IconBox from "components/icons/IconBox";
import React, { useEffect, useState } from "react";
import {
  MdAddTask,
  MdAttachMoney,
  MdBarChart,
  MdFileCopy,
} from "react-icons/md";
import CheckTable from "views/admin/default/components/CheckTable";
import ComplexTable from "views/admin/default/components/ComplexTable";
import DailyTraffic from "views/admin/default/components/DailyTraffic";
import PieCard from "views/admin/default/components/PieCard";
import Tasks from "views/admin/default/components/Tasks";
import TotalSpent from "views/admin/default/components/TotalSpent";
import WeeklyRevenue from "views/admin/default/components/WeeklyRevenue";
import {
  columnsDataCheck,
  columnsDataComplex,
} from "views/admin/default/variables/columnsData";
import tableDataCheck from "views/admin/default/variables/tableDataCheck.json";
import tableDataComplex from "views/admin/default/variables/tableDataComplex.json";
import { iex } from "configs1/iex";

let USDollar = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
});

export default function UserReports() {
  // Chakra Color Mode
  const brandColor = useColorModeValue("brand.500", "white");
  const boxBg = useColorModeValue("secondaryGray.300", "whiteAlpha.100");
  // const Alpaca = require("@alpacahq/alpaca-trade-api");
  // const alpaca = new Alpaca();
  const accountUrl = `${iex.base_url}/v2/account`;
  const portHistoryUrl = `${iex.base_url}/v2/account/portfolio/history`;
  const portHistoryUrlY = `${iex.base_url}/v2/account/portfolio/history?period=1y`;
  const portHistoryUrlD= `${iex.base_url}/v2/account/portfolio/history?period=1d`;

  const positionsUrl = `${iex.base_url}/v2/positions`;
  const ordersUrl = `${iex.base_url}/v2/orders?status=closed`;
  const [account, setAccount] = useState({});
  const [portHistory, setPortHistory] = useState({});
  const [positions, setPositions] = useState([]);
  const [orders, setOrders] = useState([]);
  const fetchPortHistory = (period) => {
    const url = `${iex.base_url}/v2/account/portfolio/history?period=${period}`;
  
    fetch(url, {
      headers: {
        "Apca-Api-Key-Id": iex.api_token,
        "Apca-Api-Secret-Key": iex.api_secret_key,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
        setPortHistory(data);
      });
  };
  useEffect(() => {
    // Fetch account data
    fetch(accountUrl, {
      headers: {
         "Apca-Api-Key-Id": iex.api_token,
         "Apca-Api-Secret-Key": iex.api_secret_key
      }
    })
    .then((response)=>response.json())
    .then((data) => {
        console.log(data);
        setAccount(data);
    });
    // // Fetch portfolio history
    // fetch(portHistoryUrl, {
    //   headers: {
    //      "Apca-Api-Key-Id": iex.api_token,
    //      "Apca-Api-Secret-Key": iex.api_secret_key
    //   }
    // })
    // .then((response)=>response.json())
    // .then((data) => {
    //     console.log(data);
    //     setPortHistory(data);
    // });
    // Fetch initial portfolio history with a default period (e.g. 1 month)
    fetchPortHistory("1m");
    // Fetch all positions 
    fetch(positionsUrl, {
      headers: {
         "Apca-Api-Key-Id": iex.api_token,
         "Apca-Api-Secret-Key": iex.api_secret_key
      }
    })
    .then((response)=>response.json())
    .then((data) => {
        console.log("positions", data);
        setPositions(data);
    });
    // Fetch orders
    fetch(ordersUrl, {
      headers: {
         "Apca-Api-Key-Id": iex.api_token,
         "Apca-Api-Secret-Key": iex.api_secret_key
      }
    })
    .then((response)=>response.json())
    .then((data) => {
        console.log("orders", data);
        setOrders(data.map(order => {order.amount = String(Number(order.filled_avg_price) * Number(order.filled_qty)); return order}));
        // setOrders(data);
    });

  }, []);

  return (
    <Box pt={{ base: "130px", md: "80px", xl: "80px" }}>
      {/* <SimpleGrid
      
      >
        <Text>Trading status:</Text>
      </SimpleGrid> */}
      <SimpleGrid
        columns={{ base: 1, md: 2, lg: 4, "2xl": 6 }}
        gap='20px'
        mb='20px'>
        <MiniStatistics
          startContent={
            <IconBox
              w='56px'
              h='56px'
              bg={boxBg}
              icon={
                <Icon w='32px' h='32px' as={MdBarChart} color={brandColor} />
              }
            />
          }
          name='Equity'
          value={USDollar.format(account.equity)}
        />
        <MiniStatistics
          startContent={
            <IconBox
              w='56px'
              h='56px'
              bg={boxBg}
              icon={
                <Icon w='32px' h='32px' as={MdAttachMoney} color={brandColor} />
              }
            />
          }
          name='Buying Power'
          value={USDollar.format(account.buying_power)}
        />
        <MiniStatistics growth={((account.equity-account.last_equity)/account.equity*100).toFixed(2)+"%"} name='Profit/Loss' value={USDollar.format(account.equity-account.last_equity)} />
        <MiniStatistics
          endContent={
            <Flex me='-16px' mt='10px'>
              <FormLabel htmlFor='balance'>
                <Avatar src={Usa} />
              </FormLabel>
              <Select
                id='balance'
                variant='mini'
                mt='5px'
                me='0px'
                defaultValue='usd'>
                <option value='usd'>USD</option>
                <option value='eur'>EUR</option>
                <option value='gba'>GBA</option>
              </Select>
            </Flex>
          }
          name='Cash'
          value={USDollar.format(account.cash)}
        />
        {/* <MiniStatistics
          startContent={
            <IconBox
              w='56px'
              h='56px'
              bg='linear-gradient(90deg, #4481EB 0%, #04BEFE 100%)'
              icon={<Icon w='28px' h='28px' as={MdAddTask} color='white' />}
            />
          }
          name='New Tasks'
          value='154'
        /> */}
        {/* <MiniStatistics
          startContent={
            <IconBox
              w='56px'
              h='56px'
              bg={boxBg}
              icon={
                <Icon w='32px' h='32px' as={MdFileCopy} color={brandColor} />
              }
            />
          }
          name='Total Projects'
          value='2935'
        /> */}
      </SimpleGrid>
      <SimpleGrid columns={{ base: 1, md: 1, xl: 1 }} gap='20px' mb='20px'>
        <TotalSpent
          data={portHistory}
          dailyUrl={portHistoryUrlD}
          monthlyUrl={portHistoryUrl}
          yearlyUrl={portHistoryUrlY}
        />
      </SimpleGrid>
      {/* <SimpleGrid columns={{ base: 1, md: 2, lg: 4, "2xl": 6 }} gap="20px" mb="20px">
        <Box>
          <Button onClick={() => fetchPortHistory("1d")}>1D</Button>
          <Button onClick={() => fetchPortHistory("1m")}>1M</Button>
          <Button onClick={() => fetchPortHistory("1y")}>1Y</Button>
        </Box>
      </SimpleGrid> */}
      <SimpleGrid columns={{ base: 1, md: 1, xl: 1 }} gap='20px' mb='20px'>
        <CheckTable columnsData={columnsDataCheck} tableData={positions} />
        {/* <SimpleGrid columns={{ base: 1, md: 2, xl: 2 }} gap='20px'>
          <DailyTraffic />
          <PieCard />
        </SimpleGrid> */}
      </SimpleGrid>
      <SimpleGrid columns={{ base: 1, md: 1, xl: 1 }} gap='20px' mb='20px'>
        <ComplexTable
          columnsData={columnsDataComplex}
          // tableData={tableDataComplex}
          tableData={orders}
        />
        <SimpleGrid columns={{ base: 1, md: 2, xl: 2 }} gap='20px'>
          <Tasks />
          <MiniCalendar h='100%' minW='100%' selectRange={false} />
        </SimpleGrid>
      </SimpleGrid>
    </Box>
  );
}

